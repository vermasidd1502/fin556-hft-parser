# fin556-hft-parser

Fast parsers for **Nasdaq TotalView-ITCH 5.0** and **CME Globex MDP 3.0** packet captures (`.pcap.zst`),
built for a leveraged-ETF microstructure project (NQ futures vs QQQ / TQQQ / SQQQ) in UIUC FIN556
*Algorithmic Market Microstructure*, Fall 2026.

> **No market data is included.** This repo is code only. You need your own licensed captures.

**New here? Follow [GETTING_STARTED.md](GETTING_STARTED.md)**: every terminal step with its expected output.

## What it does
For each trading day it rebuilds the order books and writes, on one nanosecond clock:
- every top-of-book change and trade for the chosen Nasdaq symbols (ITCH) and CME contracts (MDP 3.0)
- a merged **long** file (every update) and a **wide** file (one row per time step, symbols side by side)
- optional **bars** (1/5/10/60 min) and **window ticks** for many symbols (`make_bars.py`)

## v2 architecture
```
reader thread   mmap .pcap.zst -> in-process zstd -> 8 MB preallocated blocks
      | lock-free SPSC ring (full)      <- SPSC ring (empty, recycled)
parser thread   pcap -> Ethernet/IP/UDP -> MoldUDP64 / MDP3 -> order books -> CSV rows
      | lock-free SPSC ring (full)      <- SPSC ring (empty, recycled)
writer thread   the only thread that calls write()
```
- No thread mixes read and write syscalls; no per-packet syscalls; no allocation after start-up
- Acquire/release ordering only; producer/consumer indices on separate cache lines; optional `--pin r,p,w`
- Many days: `run_days.py` drains a job queue with a worker pool capped at 32 threads

**v1 is the unit test.** `itch_fast` / `mdp3_fast` (single-threaded) are kept as the reference; v2 must
reproduce their output byte-for-byte.

| Check | Result |
|---|---|
| v1 vs v2 output, real ITCH file (34.6M packets) | byte-identical |
| v1 vs v2 output, synthetic ITCH + CME (dupes, multi-file, snapshots) | byte-identical |
| One 10-min ITCH file, course VM | 5.36 s → 2.99 s (**1.8×**) |

## Build
```bash
./build.sh          # builds v1 and v2; v2 links libzstd (falls back to stdin mode without it)
```
Python side: `pip install pandas pyarrow numpy zstandard`

## Use
```bash
# one day, NQ + QQQ/TQQQ/SQQQ, 04:00-20:00 New York time
python3 ndx_combine.py --from 20250402 --to 20250402 --start 04:00 --end 20:00 --nq-secids NQM5=<SecurityID>

# many days through the 32-thread job queue, cleaning raw files as it goes
python3 run_days.py --from 20250401 --to 20250430 --nq-secids NQM5=<SecurityID> --clean-raw

# 5-minute bars + every tick in a window for many symbols
python3 make_bars.py --date 20250402 --bar-min 5 --start 18:00 --end 20:00 --ticks --symbols QQQ,TQQQ,SQQQ,NVDA

# find a CME contract's SecurityID when captures carry no definitions
python3 mdp3_parse.py --discover --px-min 1500000 --px-max 3000000 --max-packets 3000000 <glbx file>
```

## Files
| File | Role |
|---|---|
| `pipeline.hpp` | reader / SPSC ring / writer stages shared by v2 |
| `itch_fast2.cpp`, `mdp3_fast2.cpp` | v2 multithreaded parsers |
| `itch_fast.cpp`, `mdp3_fast.cpp` | v1 single-threaded reference |
| `ndx_combine.py` | per-day driver: runs both parsers, merges to long/wide parquet |
| `run_days.py` | job queue + capped worker pool for many days |
| `make_bars.py` | bars and window ticks for many symbols, streaming through pipes |
| `itch_zst_parse.py`, `mdp3_parse.py` | pure-Python parsers (slower; discover mode) |
| `fast_feed.py`, `view_table.py`, `build.sh` | helpers |
| `CLAUDE.md` | rules for the AI coding agent working on this repo |

## Notes
- CME captures without instrument definitions: select contracts by SecurityID; it changes at each roll.
- CME index-future prices may need `--display-factor 0.01`.
- Nasdaq output is Nasdaq's own book, not the consolidated tape.

Built by Group 8 with AI coding agents. THIS IS HFT! NOT SHEEPLE CODING!!!
