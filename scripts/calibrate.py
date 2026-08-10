#!/usr/bin/env python3
"""Difficulty calibration report from data/responses.db.

Groups responses by category and difficulty params (seed excluded), and
reports count, accuracy, median seconds, and the most common error tag.

Run from the repo root:  python scripts/calibrate.py
"""
import json
import sqlite3
import statistics
from collections import Counter
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "data" / "responses.db"


def main():
    if not DB.exists():
        print(f"no database at {DB} — answer some questions in the app first")
        return
    with sqlite3.connect(DB) as conn:
        rows = conn.execute(
            "SELECT category, params, error_tag, correct, seconds FROM responses"
        ).fetchall()
    if not rows:
        print("responses.db exists but holds no responses yet")
        return

    groups = {}
    for cat, params, tag, correct, secs in rows:
        knobs = {k: v for k, v in json.loads(params).items() if k != "seed"}
        key = (cat, json.dumps(knobs, sort_keys=True))
        groups.setdefault(key, []).append((tag, correct, secs))

    kw = max(len(k) for _, k in groups)
    header = (f"{'category':<24} {'difficulty params':<{kw}} "
              f"{'n':>4} {'acc':>5} {'median':>7}  most common error")
    print(header)
    print("-" * len(header))
    for (cat, knobs), resp in sorted(groups.items()):
        n = len(resp)
        acc = sum(c for _, c, _ in resp) / n
        med = statistics.median(s for _, _, s in resp)
        errs = Counter(t for t, c, _ in resp if not c and t)
        top = (f"{errs.most_common(1)[0][0]} ({errs.most_common(1)[0][1]}x)"
               if errs else "-")
        print(f"{cat:<24} {knobs:<{kw}} {n:>4} {acc:>5.0%} {med:>6.1f}s  {top}")


if __name__ == "__main__":
    main()
