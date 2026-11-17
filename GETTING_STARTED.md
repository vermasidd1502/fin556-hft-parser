# Getting started: step-by-step terminal guide

Every command below runs in a Linux terminal (the course lab VM, reached through the VPN and Guacamole).
Each step shows what you should see. Times are New York time unless noted.

---

## 1. One-time setup

### 1.1 Python environment
```bash
python3 --version                      # needs 3.9 or newer
python3 -m venv ~/letf_env
source ~/letf_env/bin/activate         # your prompt now starts with (letf_env)
pip install pandas pyarrow numpy zstandard
python3 -c "import pandas, pyarrow, numpy, zstandard; print('PYTHON OK')"
```
Expected: `PYTHON OK`. Run `source ~/letf_env/bin/activate` again in every new terminal.

### 1.2 Get the code and build
```bash
git clone https://github.com/vermasidd1502/fin556-hft-parser.git
cd fin556-hft-parser
./build.sh
```
Expected:
```
itch_fast2: built with libzstd (reads .pcap.zst itself)
mdp3_fast2: built with libzstd (reads .pcap.zst itself)
BUILD OK
```

### 1.3 Check the data is there
```bash
ls /db_pcaps/xnas_pcaps | head -3      # Nasdaq ITCH, one folder per date (YYYYMMDD)
ls /db_pcaps/glbx_pcaps | head -3      # CME MDP 3.0
ls /db_pcaps/xnas_pcaps/20250402 | head -3
```
Expected: date folders, then 10-minute files such as `ny4-xnas-tvitch-a-20250402T150000.pcap.zst`.

---

## 2. Unit test: v2 must match v1 exactly
```bash
mkdir -p ~/v2check
F=$(ls /db_pcaps/xnas_pcaps/20250402/*T150000*.zst | head -1)
time python3 fast_feed.py ./itch_fast --symbols QQQ,TQQQ,SQQQ --out ~/v2check/v1 -- $F 2>/dev/null
time ./itch_fast2 --symbols QQQ,TQQQ,SQQQ --out ~/v2check/v2 -- $F 2>/dev/null
for f in bbo trades; do cmp -s ~/v2check/v1_$f.csv ~/v2check/v2_$f.csv && echo "$f IDENTICAL" || echo "$f DIFFER"; done
rm -rf ~/v2check
```
Expected: two `real` times (v2 lower; about 5.4 s vs 3.0 s on the lab VM), then:
```
bbo IDENTICAL
trades IDENTICAL
```

---

## 3. Find the futures contract ID (once per quarterly contract)
The CME captures carry no instrument definitions, so the NQ contract is chosen by its SecurityID.
```bash
F=$(ls /db_pcaps/glbx_pcaps/20250402/*T15* | head -1)
python3 mdp3_parse.py --discover --px-min 1500000 --px-max 3000000 --max-packets 3000000 "$F"
```
Expected: a table of candidate IDs. Two rows trade at the same price: the full-size NQ shows fewer trades
and quote sizes of about 1–4 contracts; the micro (MNQ) shows more trades and bigger sizes. For April 2025:
NQM5 = 42005804, MNQM5 = 42009475.

---

## 4. Parse one full day (about 1 hour)
```bash
nohup python3 run_days.py --from 20250403 --to 20250403 --nq-secids NQM5=42005804 \
      --start 04:00 --end 20:00 --clean-raw > days.log 2>&1 &
tail -3 days.log                       # check progress any time
```
Expected right away: `1 day(s) queued; 1 worker(s) x 6 threads (cap …)`.
When done: `20250403: ok in XX min` and `finished 1/1 day(s)`. The per-day log is in `out/logs/`:
```bash
tail -8 out/logs/run_20250403.log
```
Expected: one check line per symbol with `crossed quotes 0`, then the two output files:
`out/ndx_long_20250403.parquet` (every update) and `out/ndx_wide_20250403.parquet` (100 ms grid).

Many days: change `--from/--to`. Up to 5 days run at once (32-thread cap ÷ 6 threads per day).

---

## 5. Bars and window ticks for many symbols
```bash
# 5-minute bars, full day, 20 symbols + NQ (reuses the NQ parse from step 4)
python3 make_bars.py --date 20250403 --bar-min 5

# the quiet window 5-7 pm Chicago (= 18:00-20:00 New York): 1-minute bars + every tick
python3 make_bars.py --date 20250403 --bar-min 1 --start 18:00 --end 20:00 --ticks \
        --symbols QQQ,TQQQ,SQQQ,NVDA,NVDL,TSLA,TSLL
```
Expected: one summary line per symbol, then `wrote … rows -> out/bars_5min_20250403.txt`, and with
`--ticks` also `out/ticks_20250403_1800-2000.txt.gz`. Later bar sizes for the same day take seconds.

Look at a result:
```bash
head -5 out/bars_5min_20250403.txt
python3 view_table.py out/ndx_wide_20250403.parquet     # opens as a table in the browser
```

---

## 6. Keep the shared disk healthy
```bash
df -h /                                # check before every big job
du -sh out/ out/raw/                   # your own usage
```
Raw CSVs are deleted automatically with `--clean-raw`. Move finished results to your approved storage
and delete them from the VM. Never commit data to git (the `.gitignore` blocks it).

---

## 7. Optional: let an AI agent run it (Claude Code on the VM)
```bash
curl -fsSL https://claude.ai/install.sh | bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
cd fin556-hft-parser && claude          # first run: /login, open the link in the VM browser, paste the code
```
Claude reads `CLAUDE.md` (HFT coding rules, disk rules, token-saving work mode) every time it starts.
Example request:
> Run the unit test from GETTING_STARTED.md step 2 and report only IDENTICAL/DIFFER and both times.

---

## Troubleshooting
| You see | Fix |
|---|---|
| `No module named pandas` | `source ~/letf_env/bin/activate` |
| `itch_fast2 is not built` | `./build.sh` |
| `built WITHOUT libzstd` | still works: pipe input with `zstd -dc file \| ./itch_fast2 ...` |
| `no Nasdaq files found` | wrong date or a weekend: `ls /db_pcaps/xnas_pcaps` |
| `WARNING: XXXX: no data that day` | that ticker wasn't trading on that date |
| disk nearly full | delete `out/raw/*`, move results off the VM, rerun with `--clean-raw` |
