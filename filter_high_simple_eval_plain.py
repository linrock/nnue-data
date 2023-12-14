import os.path
import sys

''' Filters for only positions with high abs(simple_eval)
'''

# abs(simple_eval) needs to be higher than this to keep the position
MIN_SIMPLE_EVAL_THRESHOLD = 1000

# https://github.com/official-stockfish/Stockfish/blob/master/src/types.h#L179-L183
PAWN = 208
KNIGHT = 781
BISHOP = 825
ROOK = 1276
QUEEN = 2538


def get_simple_eval(fen_str):
    simple_eval = 0
    for sq in fen_str:
        match sq:
            case 'b': simple_eval += BISHOP
            case 'B': simple_eval -= BISHOP

            case 'n': simple_eval += KNIGHT
            case 'N': simple_eval -= KNIGHT

            case 'r': simple_eval += ROOK
            case 'R': simple_eval -= ROOK

            case 'q': simple_eval += QUEEN
            case 'Q': simple_eval -= QUEEN
    return simple_eval


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: ./filter_plain.py <input.plain>')
        sys.exit(0)

    input_filename = sys.argv[1]
    output_filename = input_filename.replace('.plain', '.filtered-high-simple-eval.plain')

    if os.path.isfile(output_filename):
        print(f'Found filtered file. Doing nothing: {output_filename}')
        sys.exit(0)

    position = None
    num_positions = 0
    num_filtered_positions = 0

    print(f'Filtering {input_filename} ...')
    with open(input_filename, 'r') as infile, open(output_filename, 'w+') as outfile:
        for row in infile:
            if row.startswith('fen'):
                position = row
            else:
                position += row
                if row == 'e\n':
                    num_positions += 1
                    fen_str = position.split(' ')[1]
                    simple_eval = get_simple_eval(fen_str)
                    if abs(simple_eval) > MIN_SIMPLE_EVAL_THRESHOLD:
                        # any position with simple eval is ok
                        num_filtered_positions += 1
                        outfile.write(position)
                    if num_positions % 100_000 == 0:
                        print(f'{num_positions} positions processed. # high simple eval: {num_filtered_positions}')

    print(f'Filtered {input_filename} to {output_filename}')
    print(f'simple eval > {MIN_SIMPLE_EVAL_THRESHOLD}')
    print(f'  # positions:             {num_positions}')
    print(f'  # high simple eval:      {num_filtered_positions}')
