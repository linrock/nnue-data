#!/bin/bash
if [ "$#" -ne 1 ]; then
  echo "Usage: ./minimize_binpack.sh <input_binpack>"
  exit 0
fi

input_binpack=$1

options="
uci
setoption name Threads value 32
isready
transform minimize_binpack input_file ${input_binpack} output_file ${input_binpack}.min.binpack
quit"

printf "$options" | stockfish-bin-min
