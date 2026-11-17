#!/usr/bin/env python3
"""view_table.py - open a parsed output file as a scrollable table in the browser (nothing is uploaded anywhere).

  python3 view_table.py out/ndx_wide_20250203.parquet            # compact view: time + bid/ask of NQ, QQQ, TQQQ, SQQQ
  python3 view_table.py out/ndx_wide_20250203.parquet --all      # every column
  python3 view_table.py out/ndx_long_20250203.parquet --rows 20000
It writes <file>.html next to the input and opens it with xdg-open if that exists.
"""
import argparse
import os
import shutil
import subprocess

import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("file", help=".parquet or .csv")
ap.add_argument("--all", action="store_true", help="show every column (wide file only)")
ap.add_argument("--rows", type=int, default=0, help="only the first N rows (default: all; long files are huge, use e.g. 20000)")
a = ap.parse_args()
df = pd.read_parquet(a.file) if a.file.endswith(".parquet") else pd.read_csv(a.file)
if a.rows:
    df = df.head(a.rows)
if not a.all and "time_et" in df.columns and "NQH5_bid_px" in df.columns:
    df = df[["time_et"] + [f"{s}_{c}" for s in ("NQH5", "QQQ", "TQQQ", "SQQQ") for c in ("bid_px", "ask_px")]]
for c in df.columns:
    if "datetime" in str(df[c].dtype):
        df[c] = df[c].dt.strftime("%H:%M:%S.%f")
out = os.path.splitext(a.file)[0] + ".html"
css = "<style>body{font:13px monospace}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:2px 6px;text-align:right}th{background:#eee;position:sticky;top:0}</style>"
with open(out, "w") as fh:
    fh.write(css + df.to_html(index=False, float_format=lambda x: f"{x:.4f}".rstrip("0").rstrip(".")))
print(f"wrote {out}  ({len(df):,} rows, {len(df.columns)} columns)")
if shutil.which("xdg-open"):
    subprocess.Popen(["xdg-open", out])
else:
    print("open it in the browser:  file://" + os.path.abspath(out))
