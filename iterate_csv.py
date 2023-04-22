import io
import os.path
import sys

import chess
import zstandard

''' Iterate over positions .csv files and output .plain files
'''
if len(sys.argv) != 2:
    print('Usage: ./iterate_csv.py <input_csv_file>')
    sys.exit(0)

input_filename = sys.argv[1]
if input_filename.endswith(".csv"):
    output_filename = input_filename.replace('.csv', '.csv.plain')
elif input_filename.endswith(".csv.zst"):
    output_filename = input_filename.replace('.csv.zst', '.csv.zst.plain')

if os.path.isfile(output_filename):
    print(f'Found .csv.plain file. Doing nothing: {output_filename}')
    sys.exit(0)

position = None
num_games = 0
num_positions = 0
num_positions_filtered_out = 0
num_bestmove_captures = 0
num_bestmove_promos = 0
num_sf_bestmove1_captures = 0
num_sf_bestmove2_captures = 0

is_standard_game = False
num_standard_games = 0
num_non_standard_games = 0

def move_is_promo(uci_move):
    return len(uci_move) == 5 and uci_move[-1] in ['n','b','r','q']

def process_csv_rows(infile):
    global num_games, num_positions, num_positions_filtered_out, \
           num_bestmove_captures, num_bestmove_promos, num_sf_bestmove1_captures, num_sf_bestmove2_captures, \
           num_standard_games, num_non_standard_games
    for row in infile:
        ply, fen, bestmove_uci, bestmove_score, game_result, \
        sf_search_method, sf_bestmove1_uci, sf_bestmove1_score, sf_bestmove2_uci, sf_bestmove2_score = \
            row.strip().split(",")
        ply = int(ply)
        if ply == 0:
            num_games += 1
            if 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq' in fen:
                num_standard_games += 1
            else:
                num_non_standard_games += 1
        b = chess.Board(fen)
        bestmove = chess.Move.from_uci(bestmove_uci)
        # check if provided move is a capture or promo
        bestmove_is_capture = b.is_capture(bestmove)
        should_filter_out = False
        if bestmove_is_capture:
            num_bestmove_captures += 1
            should_filter_out = True
        bestmove_is_promo = move_is_promo(bestmove_uci)
        if bestmove_is_promo:
            num_bestmove_promos += 1
            should_filter_out = True
        # check if moves from SF search are captures or promos
        sf_bestmove1 = chess.Move.from_uci(sf_bestmove1_uci)
        if b.is_capture(sf_bestmove1):
            num_sf_bestmove1_captures += 1
            should_filter_out = True
        b.push(sf_bestmove1)
        sf_bestmove2 = chess.Move.from_uci(sf_bestmove2_uci)
        print(f'{fen}, bm: {bestmove} ({bestmove_score}), sf_bm1: {sf_bestmove1} ({sf_bestmove1_score}), sf_bm2: {sf_bestmove2} ({sf_bestmove2_score})')
        if b.is_capture(sf_bestmove2):
            num_sf_bestmove2_captures += 1
            should_filter_out = True
        num_positions += 1
        if should_filter_out:
            num_positions_filtered_out += 1

print(f'Processing {input_filename} ...')
if input_filename.endswith(".csv.zst"):
    with open(input_filename, 'rb') as compressed_infile:
        dctx = zstandard.ZstdDecompressor()
        stream_reader = dctx.stream_reader(compressed_infile)
        text_stream = io.TextIOWrapper(stream_reader, encoding='utf-8')
        process_csv_rows(text_stream)
else:
    with open(input_filename, 'r') as infile: # , open(output_filename, 'w+') as outfile:
        process_csv_rows(infile)

print(f'Filtered {input_filename} to {output_filename}')
print(f'  # games:                       {num_games}')
print(f'    # standard games:            {num_standard_games}')
print(f'    # non-standard games:        {num_non_standard_games}')
print(f'  # positions:                   {num_positions}')
print(f'    # bestmove captures:         {num_bestmove_captures}')
print(f'    # bestmove promos:           {num_bestmove_promos}')
print(f'    # sf bestmove1 captures:     {num_sf_bestmove1_captures}')
print(f'    # sf re-captures after bm1:  {num_sf_bestmove2_captures}')
print(f'  # positions after filtering:   {num_positions - num_positions_filtered_out}')
