#!/bin/bash
if [ "$#" -ne 1 ]; then
  echo "Usage: ./many_binpacks_to_csv.sh <input_binpack_output_csv_dir>"
  exit 0
fi

function binpack_to_csv() {
  input_filename=$1
  output_filename=$(basename $1).csv
  output_dir=$2
  output_csv_filepath=$output_dir/$output_filename
  if [ -f $output_csv_filepath ]; then
    echo "Doing nothing, csv exists: $output_csv_filepath"
  elif [ -f ${output_csv_filepath}.zst ]; then
    echo "Doing nothing, csv.zst exists: ${output_csv_filepath}.zst"
  else
    echo "Converting... $input_filename -> .csv"
    ./binpack_to_csv.sh $input_filename | grep "d6 pv2" > $output_csv_filepath
  fi
}
export -f binpack_to_csv

# Converts binpacks to csv with search eval data for each position
concurrency=$(( $(nproc) - 1 ))
ls -1v $1/*.binpack | xargs -P $concurrency -I{} bash -c 'binpack_to_csv "$@"' _ {} $1
