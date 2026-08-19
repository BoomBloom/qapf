"""Ticket 13 — build the real point-in-time S&P 500 universe.

Runs Qlib's own vendored PIT-constituents collector
(reference/qlib/scripts/data_collector/us_index/collector.py), but with one
necessary patch discovered while running it for real, not assumed from the
research that flagged this collector as "free and already vendored"
(docs/research/data-and-modelling-tooling.md): Wikipedia's "List of S&P 500
companies" article no longer has a "Selected changes" section AT ALL as of
2026 -- verified directly (fetched the live page, `pd.read_html` returns only
2 tables: current constituents and an unrelated nav template; the MediaWiki
API's own section list confirms no such section exists anymore). The
collector's `get_changes()` depends entirely on that table, so it crashes
with `IndexError: positional indexers are out-of-bounds` against the live
page -- not a bug in this project's code, a real content change upstream.

THE FIX: Wikipedia keeps full revision history. The changes table existed as
of the 2024-05-23 revision (id 1225357006, verified by fetching it directly
and confirming a 345-row table with the exact columns the collector expects:
Date / Added Ticker / Added Security / Removed Ticker / Removed Security /
Reason, covering 1997-06-17 through 2024-05-08 -- 189 of those 345 changes
fall inside this project's 2008-2017 validation window, including real,
well-known events the current hand-picked universe completely misses:
Lehman Brothers' 2008-09-16 removal, Fannie Mae/Freddie Mac's 2008-09-12
removal (conservatorship), Wachovia's 2008-12-31 removal (Wells Fargo
acquisition). This is exactly the survivorship-bias gap ticket 10 exists to
close -- these are precisely the names a 2026-hindsight-picked universe would
never include.

So: subclass `SP500Index`, override just `WIKISP500_CHANGES_URL` to point at
that specific historical revision instead of the live page. Nothing else in
the collector's logic needs to change -- the column positions
(`iloc[:, [0, 1, 3]]` = Date, Added Ticker, Removed Ticker) still line up
correctly against the old table's structure.

Needs reference/qlib on PYTHONPATH ahead of the pip-installed `pyqlib`
package (0.9.7) -- the vendored collector script imports
`qlib.utils.pickle_utils.restricted_pickle_load`, which doesn't exist in the
PyPI 0.9.7 release, only in this project's newer reference/qlib checkout.
Isolated to this one standalone script's subprocess; does not touch
backend/'s runtime `import qlib`, which is unaffected and stays pinned to the
pip-installed package as before.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QLIB_REPO = REPO_ROOT / "reference" / "qlib"
QLIB_SCRIPTS = QLIB_REPO / "scripts"

# Order matters: reference/qlib's checkout must resolve `import qlib` before
# the pip-installed pyqlib 0.9.7 does (see module docstring).
sys.path.insert(0, str(QLIB_REPO))
sys.path.insert(0, str(QLIB_SCRIPTS))

# Verified 2026-08-19 by fetching this exact revision directly (see module
# docstring): has the full 345-row historical changes table with the exact
# column layout this collector's get_changes() expects.
HISTORICAL_REVISION_URL = "https://en.wikipedia.org/wiki/Special:Redirect/revision/1225357006"


def build(qlib_dir: str = "~/.qlib/qlib_data/us_data"):
    from data_collector.us_index.collector import SP500Index

    class SP500IndexPointInTime(SP500Index):
        """Same as SP500Index, except get_changes() fetches a historical
        Wikipedia revision (the live page's changes table is gone) rather
        than a hand-maintained scrape -- see module docstring."""

        WIKISP500_CHANGES_URL = HISTORICAL_REVISION_URL

    collector = SP500IndexPointInTime(index_name="SP500", qlib_dir=qlib_dir)
    collector.parse_instruments()

    out_path = collector.instruments_dir.joinpath("sp500.txt")
    print(f"\nWrote {out_path}")
    return out_path


def verify(out_path):
    """Real correctness check, not a trust-the-tool assumption: the
    point-in-time file must actually contain names removed before 2026 --
    that's the entire property this ticket exists to add. If it doesn't,
    the fix didn't work, regardless of whether the script exited cleanly."""
    import pandas as pd

    df = pd.read_csv(out_path, sep="\t", header=None, names=["symbol", "start_date", "end_date"])
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")

    print(f"\n{len(df)} symbol-interval rows loaded (a symbol can appear more than once "
          f"if it left and rejoined the index).")

    # Known, independently-verifiable 2008 removals -- not chosen because
    # they're famous, chosen because they're objectively verifiable
    # (bankruptcy/acquisition are public record) and were in the S&P 500
    # exactly during this project's 2008-2017 validation window.
    known_gone_by_2026 = {
        "LEH": "Lehman Brothers, bankrupt Sept 2008",
        "FNM": "Fannie Mae, conservatorship Sept 2008",
        "FRE": "Freddie Mac, conservatorship Sept 2008",
        "WB": "Wachovia, acquired by Wells Fargo Dec 2008",
    }
    still_open_ended = df[df["end_date"].isna() | (df["end_date"] > pd.Timestamp("2026-01-01"))]
    still_open_symbols = set(still_open_ended["symbol"])

    all_ok = True
    for sym, why in known_gone_by_2026.items():
        rows = df[df["symbol"] == sym]
        if rows.empty:
            print(f"  [FAIL] {sym} ({why}) -- not present in the PIT file at all.")
            all_ok = False
            continue
        max_end = rows["end_date"].max()
        if sym in still_open_symbols:
            print(f"  [FAIL] {sym} ({why}) -- present but with no real removal date (looks still-active).")
            all_ok = False
        else:
            print(f"  [PASS] {sym} ({why}) -- removal date {max_end.date()} correctly captured.")

    assert all_ok, "PIT universe file failed real-removal verification -- see FAILs above."
    print("\nAll known-removal checks PASSED -- this file actually encodes point-in-time membership, "
          "not just a relabeled current constituent list.")


if __name__ == "__main__":
    out_path = build()
    verify(out_path)
