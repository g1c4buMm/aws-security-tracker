#!/usr/bin/env python3
"""Merge a week file (data/weeks/wNN.json) into data/launches.json.

Usage:  python3 scripts/add_week.py data/weeks/w41.json

Each entry needs: d (YYYY-MM-DD), t (official title), u (official URL),
p (pillar), s (service), x (one-line summary from the official text).
The ISO week (w) is computed from the date. Entries whose URL already
exists are skipped, so running the script twice is safe.
"""
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "launches.json"
PILLARS = {"threat", "identity", "posture", "network", "data", "ai"}
FIELDS = ("d", "t", "u", "p", "s", "x")


def iso_week(day: str) -> int:
    year, week, _ = dt.date.fromisoformat(day).isocalendar()
    if year != 2026:
        sys.exit(f"{day} falls in ISO year {year}; this tracker covers 2026 only")
    return week


def validate(e: dict, i: int) -> None:
    missing = [f for f in FIELDS if not str(e.get(f, "")).strip()]
    if missing:
        sys.exit(f"entry {i}: missing {missing}")
    if e["p"] not in PILLARS:
        sys.exit(f"entry {i}: pillar '{e['p']}' not in {sorted(PILLARS)}")
    if not e["u"].startswith("https://aws.amazon.com/"):
        sys.exit(f"entry {i}: URL must be an official aws.amazon.com link")
    for ch in "—–":
        if ch in e["t"] + e["x"]:
            sys.exit(f"entry {i}: remove en/em dashes from title or summary")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    new = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    db = json.loads(DB.read_text(encoding="utf-8"))
    known = {r["u"].rstrip("/").lower() for r in db}
    added = 0
    for i, e in enumerate(new):
        validate(e, i)
        key = e["u"].rstrip("/").lower()
        if key in known:
            print(f"skip (already present): {e['t']}")
            continue
        db.append({"d": e["d"], "w": iso_week(e["d"]), **{k: e[k] for k in ("t", "u", "p", "s", "x")}})
        known.add(key)
        added += 1
    db.sort(key=lambda r: (r["d"], r["t"]))
    DB.write_text(json.dumps(db, ensure_ascii=False, indent=1), encoding="utf-8")
    weeks = sorted({r["w"] for r in db})
    print(f"added {added}; total {len(db)} launches; weeks {weeks[0]}-{weeks[-1]}")


if __name__ == "__main__":
    main()
