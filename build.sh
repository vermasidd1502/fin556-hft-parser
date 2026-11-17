#!/bin/bash
# build.sh - compile v1 (reference / unit test) and v2 (multithreaded) parsers.  Run once on the VM.
set -e
cd "$(dirname "$0")"
FLAGS="-O3 -march=native -std=c++17 -pthread"
g++ -O3 -std=c++17 -o itch_fast itch_fast.cpp
g++ -O3 -std=c++17 -o mdp3_fast mdp3_fast.cpp
for p in itch_fast2 mdp3_fast2; do
  if   g++ $FLAGS -o $p $p.cpp -l:libzstd.so.1 2>/dev/null; then echo "$p: built with libzstd (reads .pcap.zst itself)"
  elif g++ $FLAGS -o $p $p.cpp -lzstd          2>/dev/null; then echo "$p: built with libzstd (reads .pcap.zst itself)"
  else g++ $FLAGS -DNO_ZSTD -o $p $p.cpp;                       echo "$p: built WITHOUT libzstd - pipe 'zstd -dc file |' into it"
  fi
done
echo "BUILD OK"
