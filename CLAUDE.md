# Group 8 — FIN556 leveraged-ETF microstructure (lab VM)

# THIS IS HFT! NOT SHEEPLE CODING!!!
Latency, throughput and correctness first. Every piece of code here is held to that bar.

## Coding rules (from Prof. Lariviere)
- Never have one thread doing both the read and the write system calls. Minimum: reader → parser → writer
  threads joined by lock-free single-producer/single-consumer rings (see `pipeline.hpp`).
- Large-block / memory-mapped I/O, decompress in-process; no system call per packet.
- Preallocate everything; no heap allocation in hot loops; binary data in the hot path, text only at the end.
- Many days/files: a job queue with a worker pool capped at 32 threads (`run_days.py`), not one process per day.
- Start simple, prove it correct, then use it as the unit test: `itch_fast` / `mdp3_fast` (v1) are the
  reference. Any new version must reproduce v1 output byte-for-byte (`cmp`) before it replaces it.

## Data facts
- Captures: `/db_pcaps/xnas_pcaps/YYYYMMDD/*.pcap.zst` (Nasdaq TotalView-ITCH 5.0) and
  `/db_pcaps/glbx_pcaps/YYYYMMDD/*.pcap.zst` (CME MDP 3.0). 10-minute files named by UTC start time.
- CME captures carry no instrument definitions: pick NQ by SecurityID. NQM5 (Apr–mid-Jun 2025) = 42005804;
  NQH5 (Feb–mid-Mar) = 42288528. MNQM5 = 42009475. Find others with `mdp3_parse.py --discover`.
- CME index-future prices come 100× too large: `--display-factor 0.01`.
- All windows are given in New York time. The professor's quiet window 5–7 pm Chicago = 18:00–20:00 ET.
- Nasdaq data is Nasdaq's own book only (not consolidated). No NYSE/Arca data exists.

## Disk: the VM's main drive is tiny and shared by every student (professor, 16 Nov)
- Run `df -h /` before starting any job and at every check-in. Report free space in one line.
- Estimate a job's output size before starting it. If it would leave less than 5 GB free, or push the drive
  past 90%, don't start it: tell me and suggest the leaner way.
- While a job runs, if free space drops below 5 GB, stop starting new work and tell me straight away.
- Prefer streaming: pipes, in-memory aggregation, per-minute summaries, `--clean-raw`. Never leave
  intermediate raw CSVs behind once the parquet/bars they feed are written.
- Big outputs go to Box or to extra space the professor sets up, not the main drive, once that's available.
- Show our own usage with `du -sh . out/` when asked.

## Keep our folders clean
- Layout: code in this repo folder, results in `out/` (a link), logs in `out/logs/`. Nothing loose in `~`.
- After every task, delete what that task created temporarily: scratch dirs (e.g. `~/v2check`), `*.b64`,
  extracted zips already unpacked, test outputs, pip cache (`pip cache purge`).
- Before deleting anything that isn't clearly temporary (results, source folders, other people's files),
  list it with sizes and ask first. Never touch files outside this user's home.
- End each task with a one-line "cleaned: …" note listing what was removed.

## Shared VM etiquette
- Keep CPU use within the 32-thread cap. Work only inside this user's home folders.
- Python packages live in `~/letf_env` (`source ~/letf_env/bin/activate`).

## Work mode: code does the heavy lifting, you orchestrate (saves tokens)
- Never read data files or big logs into the conversation. Look only at short summaries:
  `tail -5`, `wc -l`, `head -3`, `du -sh`, `df -h /`, `grep -E "IDENTICAL|DIFFER|ok|FAILED|finished|crossed"`.
- Need a number (row count, timing, price check)? Write or reuse a small script that prints just that number.
- Long jobs (over ~1 minute) run with `nohup … &`. Start them, say how to check, then stop. Never wait or
  poll in a loop; the user will ask for status later.
- Reuse existing tools first: build.sh, itch_fast(2), mdp3_fast(2), fast_feed.py, ndx_combine.py, run_days.py,
  make_bars.py, view_table.py. Write new code only when none of them can do the job, and keep it in this folder.
- Read only the part of a source file you need (grep for the function, then read those lines), not whole files.
- Don't re-run a check that already passed, and don't re-read a file you just wrote.
- Replies: 5 lines or fewer — what ran, the result, what's next. Tables only for final results.
- One task per session; the user will `/clear` between tasks. If a session runs long, suggest `/compact`.
- Ask before anything expensive: whole-month runs, re-parsing a day that already exists, or a new big download.

## Data rules (hard)
- NEVER commit market data or outputs (pcap, zst, parquet, csv, txt bars/ticks, out/) to git. Code only.
- Results leave the VM only through Illinois Box. Never email them or copy them to personal machines.
- Don't print large chunks of raw data into the conversation; show counts, summaries and a few rows at most.
