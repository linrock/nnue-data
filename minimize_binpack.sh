#!/bin/bash
if [ "$#" -ne 1 ]; then
  echo "Usage: ./minimize_binpack.sh <input_binpack>"
  exit 0
fi

input_binpack=$1
output_binpack=${input_binpack}.min.binpack
if [ -f $output_binpack ]; then
  echo Minimized binpack already exists: $output_binpack
  exit 0
fi

options="
uci
setoption name Threads value 1
isready
transform minimize_binpack input_file ${input_binpack} output_file ${ouput_binpack}
quit"

printf "$options" | stockfish-bin-min
