from glob import glob
import io
import os
import os.path
from pprint import pprint
import re
import sys
import textwrap

import chess
import zstandard

''' Iterate over positions .csv files and output .plain files
'''
if len(sys.argv) != 2:
    print('Usage: ./csv_filter_v8.py <input_csv_file>')
    sys.exit(0)


def move_is_promo(uci_move):
    return len(uci_move) == 5 and uci_move[-1] in ['n','b','r','q']

def filter_csv_to_plain(input_filename):
    ''' Filter a .csv or .csv.zst file '''
    print(f'Processing {input_filename} ...')
    if input_filename.endswith(".csv.zst"):
        output_filename = input_filename.replace('.csv.zst', '.csv.zst.filter-v8.plain')
    else:
        output_filename = input_filename.replace('.csv', '.csv.filter-v8.plain')
    # skip filtering if the .plain file already exists
    if os.path.isfile(output_filename):
        print(f'Found .csv.zst.filter-v8.plain file, doing nothing:')
        print(output_filename)
        return
    # skip filtering if the .binpack file already exists
    binpack_filename = output_filename.replace('.csv.zst.filter-v8.plain', '.csv.zst.filter-v8.binpack')
    if os.path.isfile(binpack_filename):
        print(f'Found .csv.zst.filter-v8.binpack file, doing nothing:')
        print(binpack_filename)
        return
    # skip filtering if the minimized .min.binpack file already exists
    min_binpack_filename = binpack_filename.replace('.filter-v8.binpack', '.filter-v8.binpack.min.binpack')
    if os.path.isfile(min_binpack_filename):
        print(f'Found .csv.zst.filter-v8.binpack.min.binpack file, doing nothing:')
        print(min_binpack_filename)
        return
    # filter the file
    if input_filename.endswith(".csv.zst"):
        with open(input_filename, 'rb') as compressed_infile, \
             open(output_filename, 'w+') as outfile:
            dctx = zstandard.ZstdDecompressor()
            stream_reader = dctx.stream_reader(compressed_infile)
            text_stream = io.TextIOWrapper(stream_reader, encoding='utf-8')
            PositionCsvIterator(text_stream, outfile).process_csv_rows()
    else:
        with open(input_filename, 'r') as infile, \
             open(output_filename, 'w+') as outfile:
            PositionCsvIterator(infile, outfile).process_csv_rows()
    print(f'Saved to {output_filename}')
    return output_filename


class PositionCsvIterator:
    def __init__(self, infile, outfile):
        self.infile = infile
        self.outfile = outfile

        self.EARLY_PLY_SKIP = 36

        self.prev_ply = -1

        self.num_games = 0
        self.num_standard_games = 0
        self.num_non_standard_games = 0

        # filtering based on csv data alone
        self.num_positions = 0
        self.num_start_positions = 0
        self.num_early_plies = 0
        self.num_one_good_move = 0
        self.num_one_good_move_v8 = 0
        self.num_only_one_move = 0

        # filtering based on move types
        self.num_in_check = 0
        self.num_bestmove_promos = 0
        self.num_bestmove_captures = 0
        self.num_sf_bestmove1_capture_promos = 0
        self.num_sf_bestmove2_capture_promos = 0

        self.num_positions_filtered_out = 0

    def process_csv_row(self, csv_row):
        split_row = csv_row.strip().split(",")
        if len(split_row) == 10:
            ply, fen, bestmove_uci, bestmove_score, game_result, \
            sf_search_method, sf_bestmove1_uci, sf_bestmove1_score, \
            sf_bestmove2_uci, sf_bestmove2_score = \
                split_row
        elif len(split_row) == 8:
            # only one possible move in the position
            self.num_only_one_move += 1
            return
        ply = int(ply)
        bestmove_score = int(bestmove_score)
        sf_bestmove1_score = int(sf_bestmove1_score)
        sf_bestmove2_score = int(sf_bestmove2_score)

        # assume the dataset is a sequence of training games
        # and that we're at the beginning of a training game when this is true
        is_start_of_game = self.prev_ply == -1 or ply < self.prev_ply

        self.prev_ply = ply
        if is_start_of_game:
            # skip if it's a starting position
            if 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq' in fen:
                self.num_standard_games += 1
            else:
                self.num_non_standard_games += 1
            self.num_games += 1
            self.num_start_positions += 1
            return
        elif ply <= self.EARLY_PLY_SKIP:
            # skip if an early ply position
            self.num_early_plies += 1
            return
        # skip if there's only one good move in the position
        # (difference between best two move scores is high  enough)
        elif abs(sf_bestmove1_score) < 100 and abs(sf_bestmove2_score) > 150:
            # best move about equal, 2nd best move loses
            self.num_one_good_move += 1
            return
        elif abs(sf_bestmove1_score) > 150 and abs(sf_bestmove2_score) < 100:
            # best move gains advantage, 2nd best move equalizes
            self.num_one_good_move += 1
            return

        # if the 2 best move scores favor different sides
        elif (sf_bestmove1_score > 0) != (sf_bestmove2_score > 0):
            if abs(sf_bestmove1_score) > 150 and abs(sf_bestmove2_score) > 150:
                # best move gains an advantage, 2nd best move loses
                self.num_one_good_move += 1
                return
            elif abs(sf_bestmove1_score - sf_bestmove2_score) > 200:
                # lower score diff threshold when best moves favor different sides
                self.num_one_good_move += 1
                return
            # v8: stricter score thresholds
            if abs(sf_bestmove1_score) > 100 and abs(sf_bestmove2_score) > 100:
                # best move gains an advantage, 2nd best move loses
                self.num_one_good_move_v8 += 1
                return
            elif abs(sf_bestmove1_score - sf_bestmove2_score) > 150:
                # lower score diff threshold when best moves favor different sides
                self.num_one_good_move_v8 += 1
                return
        elif move_is_promo(bestmove_uci):
            # remove bestmove promotions
            self.num_bestmove_promos += 1
            return

        # filtering is slower when needing to initialize a board
        b = chess.Board(fen)
        if b.is_check():
            # skip if in check since eval never gets called when in check
            self.num_in_check += 1
            return
        # filter out if provided move is a capture or promo
        bestmove = chess.Move.from_uci(bestmove_uci)
        if b.is_capture(bestmove):
            self.num_bestmove_captures += 1
            return
        # check if moves from SF search are captures or promos
        sf_bestmove1 = chess.Move.from_uci(sf_bestmove1_uci)
        if b.is_capture(sf_bestmove1) or move_is_promo(sf_bestmove1_uci):
            # skip if SF search 1st best move is a capture or promo
            self.num_sf_bestmove1_capture_promos += 1
            return
        sf_bestmove2 = chess.Move.from_uci(sf_bestmove2_uci)
        if b.is_capture(sf_bestmove2) or move_is_promo(sf_bestmove2_uci):
            # skip if SF search 2nd best move is a capture or promo
            self.num_sf_bestmove2_capture_promos += 1
            return
        return (fen, bestmove_uci, bestmove_score, ply, game_result)

    def process_csv_rows(self):
        positions = []
        for row in self.infile:
            position = self.process_csv_row(row)
            self.num_positions += 1
            if position:
                (fen, bestmove_uci, bestmove_score, ply, game_result) = position
                positions.append({
                    'fen': fen,
                    'move': bestmove_uci,
                    'score': bestmove_score,
                    'ply': ply,
                    'result': game_result,
                })
            else:
                self.num_positions_filtered_out += 1
            if self.write_positions_and_print_stats(positions, self.num_positions % 100000 == 0):
                positions = []
        if self.write_positions_and_print_stats(positions, True):
            positions = []

    def write_positions_and_print_stats(self, positions, should_write) -> bool:
        if not should_write:
            return False
        self.print_stats()
        if len(positions):
            self.write_positions_to_file(positions)
            return True
        return False

    def write_positions_to_file(self, positions):
        game_plain = ''
        for position in positions:
            game_plain += textwrap.dedent(f'''
                fen {position['fen']}
                score {position['score']}
                move {str(position['move'])}
                ply {position['ply']}
                result {position['result']}
                e''')
        self.outfile.write(game_plain.strip() + "\n")

    def print_stats(self):
        num_positions_after_filter = self.num_positions - self.num_positions_filtered_out
        skip = self.EARLY_PLY_SKIP
        print(textwrap.dedent(f'''
            Processed {self.num_positions} positions
              # games:                       {self.num_games:8d}
                # standard games:            {self.num_standard_games:8d}
                # non-standard games:        {self.num_non_standard_games:8d}
              # positions:                   {self.num_positions:8d}
                # startpos:                  {self.num_start_positions:8d}
                # early plies <= {skip}:         {self.num_early_plies:8d}
                # only one move:             {self.num_only_one_move:8d}
                # one good move (v6):        {self.num_one_good_move:8d}
                # one good move (v8):        {self.num_one_good_move_v8:8d}
                # bestmove promos:           {self.num_bestmove_promos:8d}
                # bestmove captures:         {self.num_bestmove_captures:8d}
                # sf bestmove1 cap/promos:   {self.num_sf_bestmove1_capture_promos:8d}
                # sf bestmove2 cap/promos:   {self.num_sf_bestmove2_capture_promos:8d}
              # positions after filtering:   {num_positions_after_filter:8d}
                % positions kept:            {num_positions_after_filter/self.num_positions*100:8.1f}
        '''))


input_filename = sys.argv[1]
filter_csv_to_plain(input_filename)
