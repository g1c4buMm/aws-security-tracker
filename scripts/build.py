#!/usr/bin/env python3
"""Build dist/index.html from src/, i18n/ and data/launches.json.

Usage:  python3 scripts/build.py [--updated YYYY-MM-DD]

The latest week, the "Updated" date and the source date range are computed
from the data, so no HTML needs hand edits when a new week is added.
The newest data/highlights/wNN.json, written by the Security Weekly Radar,
fills the "This week's highlights" section; without one the section stays hidden.
--updated defaults to today.
"""
import argparse
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, I18N, DIST = ROOT / "src", ROOT / "i18n", ROOT / "dist"
PARTS = ["p1_head.html", "p2_top.html", "p3_deep.html", "p4_script.html"]
EN_M = "January February March April May June July August September October November December".split()
PT_M = "janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro".split()
ES_M = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()
EN_S = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
PT_S = "jan fev mar abr mai jun jul ago set out nov dez".split()
ES_S = "ene feb mar abr may jun jul ago sep oct nov dic".split()


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--updated", default=dt.date.today().isoformat())
    a = ap.parse_args()
    up = dt.date.fromisoformat(a.updated)

    data = load(ROOT / "data" / "launches.json")
    last_w = max(r["w"] for r in data)
    end = dt.date.fromisocalendar(2026, last_w, 7)  # Sunday of the latest week

    tokens = {
        "{{W}}": str(last_w),
        "{{UPDATED}}": f"{EN_M[up.month-1]} {up.day}, {up.year}",
        "{{UPDATED_PT}}": f"{up.day} de {PT_M[up.month-1]} de {up.year}",
        "{{UPDATED_ES}}": f"{up.day} de {ES_M[up.month-1]} de {up.year}",
        "{{RANGE_END}}": f"{EN_S[end.month-1]} {end.day}, {end.year}",
        "{{RANGE_END_PT}}": f"{end.day} {PT_S[end.month-1]} {end.year}",
        "{{RANGE_END_ES}}": f"{end.day} {ES_S[end.month-1]} {end.year}",
    }

    def fill(s: str) -> str:
        for k, v in tokens.items():
            s = s.replace(k, v)
        return s

    en, pt, es = load(I18N / "static_en.json"), load(I18N / "pt.json"), load(I18N / "es.json")
    static = {}
    for k in set(pt) | set(es):
        src = fill(en[int(k)])
        static[src] = {"pt": fill(pt.get(k, en[int(k)])), "es": fill(es.get(k, en[int(k)]))}
    # {{UPDATED}} in English maps to the PT/ES dates
    static[tokens["{{UPDATED}}"]] = {"pt": tokens["{{UPDATED_PT}}"], "es": tokens["{{UPDATED_ES}}"]}

    hl_files = sorted((ROOT / "data" / "highlights").glob("w*.json"), key=lambda p: int(p.stem[1:]))
    highlights = load(hl_files[-1]) if hl_files else None

    parts = {p: fill((SRC / p).read_text(encoding="utf-8")) for p in PARTS}
    html = "".join(parts.values())
    for name, obj in (("__DATA__", data), ("__STATIC__", static), ("__UI__", load(I18N / "ui.json"))):
        if name not in html:
            sys.exit(f"placeholder {name} missing in src/")
        html = html.replace(name, json.dumps(obj, ensure_ascii=False), 1)
    if "__HL__" not in html:
        sys.exit("placeholder __HL__ missing in src/")
    html = html.replace("__HL__", json.dumps(highlights, ensure_ascii=False), 1)
    if "{{" in html:
        sys.exit("unfilled token left in output")

    head_end = html.index("</style>") + len("</style>")  # p1 is head-only content
    page = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
            + html[:head_end] + "\n</head>\n<body>\n" + html[head_end:] + "\n</body>\n</html>\n")

    DIST.mkdir(exist_ok=True)
    (DIST / "index.html").write_text(page, encoding="utf-8")          # full page for Amplify / S3
    (DIST / "artifact.html").write_text(html, encoding="utf-8")       # fragment for the Claude artifact
    print(f"dist/: {len(data)} launches, weeks 1-{last_w}, updated {up}, {len(page)//1024} KB")


if __name__ == "__main__":
    main()
