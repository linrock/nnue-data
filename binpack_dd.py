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

''' Iterate over .binpack files and de-duplicate positions
'''
if len(sys.argv) < 2:
    print('Usage: ./binpack_dd.py <binpack_file_glob>')
    sys.exit(0)


piece_orientations_seen = set()

def filter_csv_to_plain(input_filename):
    ''' Filter a .csv or .csv.zst file '''
    print(f'Processing {input_filename} ...')
    if input_filename.endswith(".csv.zst"):
        output_filename = input_filename.replace('.csv.zst', '.csv.zst.filter-v6-dd.plain')
    else:
        output_filename = input_filename.replace('.csv', '.csv.filter-v6-dd.plain')
    # skip filtering if the .plain file already exists
    if os.path.isfile(output_filename):
        print(f'Found .csv.zst.filter-v6-dd.plain file, doing nothing:')
        print(output_filename)
        return
    elif os.path.isfile(output_filename.replace('.csv.zst.filter-v6-dd.plain', '.csv.zst.filter-v6-dd.binpack')):
        print(f'Found .csv.zst.filter-v6-dd.binpack file, doing nothing:')
        print(output_filename.replace('.csv.zst.filter-v6-dd.plain', '.csv.zst.filter-v6-dd.binpack'))
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
        output_filename = input_filename.replace('.csv', '.csv.filter-v6-dd.plain')
        with open(input_filename, 'r') as infile, \
             open(output_filename, 'w+') as outfile:
            PositionCsvIterator(infile, outfile).process_csv_rows()
    print(f'Saved to {output_filename}')
    return output_filename


class PositionCsvIterator:
    def __init__(self, infile, outfile):
        self.infile = infile
        self.outfile = outfile

        self.num_games = 0
        self.num_standard_games = 0
        self.num_non_standard_games = 0

        self.num_positions = 0
        self.num_start_positions = 0
        self.num_seen_before = 0
        self.num_positions_filtered_out = 0

    def process_csv_rows(self):
        global piece_orientations_seen
        positions = []
        prev_ply = -1
        for row in self.infile:
            split_row = row.strip().split(",")
            if len(split_row) == 10:
                ply, fen, bestmove_uci, bestmove_score, game_result, \
                sf_search_method, sf_bestmove1_uci, sf_bestmove1_score, \
                sf_bestmove2_uci, sf_bestmove2_score = \
                    split_row
            elif len(split_row) == 8:
                # only one possible move in the position
                self.num_only_one_move += 1
                self.num_positions += 1
                self.num_positions_filtered_out += 1
                continue
            ply = int(ply)
            bestmove_score = int(bestmove_score)
            sf_bestmove1_score = int(sf_bestmove1_score)
            sf_bestmove2_score = int(sf_bestmove2_score)

            piece_orientation = fen.split(' ')[0]
            seen_position_before = piece_orientation in piece_orientations_seen
            piece_orientations_seen.add(piece_orientation)

            should_filter_out = False

            # assume the dataset is a sequence of training games
            if ply < prev_ply:
                if 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq' in fen:
                    self.num_standard_games += 1
                else:
                    self.num_non_standard_games += 1
                self.num_games += 1
                self.num_start_positions += 1
                should_filter_out = True
            elif seen_position_before:
                # remove duplicate positions
                self.num_seen_before += 1
                should_filter_out = True
            self.num_positions += 1
            if should_filter_out:
                self.num_positions_filtered_out += 1
            else:
                positions.append({
                    'fen': fen,
                    'move': bestmove_uci,
                    'score': bestmove_score,
                    'ply': ply,
                    'result': game_result,
                })
            prev_ply = ply
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
        print(f'Processed {self.num_positions} positions')
        print(f'  # games:                       {self.num_games:8d}')
        print(f'    # standard games:            {self.num_standard_games:8d}')
        print(f'    # non-standard games:        {self.num_non_standard_games:8d}')
        print(f'  # positions:                   {self.num_positions:8d}')
        print(f'    # startpos:                  {self.num_start_positions:8d}')
        print(f'    # seen before:               {self.num_seen_before:8d}')
        print(f'  # positions after filtering:   {num_positions_after_filter:8d}')
        print(f'    % positions kept:            {num_positions_after_filter/self.num_positions*100:8.1f}')


# prioritize position scores from later in time (ie. seen end of month vs. beginning of month)
for file in sorted(glob(sys.argv[1]))[::-1]:
    filtered_plain_filename = filter_csv_to_plain(file)
    if filtered_plain_filename:
        # convert the filtered .plain file into a .binpack
        filtered_binpack_filename = filtered_plain_filename.replace('-v6-dd.plain', '-v6-dd.binpack')
        print(os.system(f"stockfish convert {filtered_plain_filename} {filtered_binpack_filename}"))
        os.system(f"rm {filtered_plain_filename}")
