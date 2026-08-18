# Qlib known issues (verified 2026-08-18, pyqlib 0.9.7)

Read this before writing any code that touches `reference/qlib` or a fork of it.

## 1. `Ref()` and other rolling-window operators silently return empty data

**Symptom:** `D.features(["AAPL"], ["$close"], ...)` returns real data. The same call with
`D.features(["AAPL"], ["Ref($close,1)"], ...)` returns an empty DataFrame — no exception, no warning
at default log level.

**Root cause:** `qlib/data/data.py` (`LocalExpressionProvider.expression`) computes an extended query
window via `Cal.locate_index(...)` and `expression.get_extended_window_size()`, then calls
`expression.load(instrument, query_start, query_end, freq)`. Under the numpy 2.x / pandas 2.3.x stack
that `pip install pyqlib` naturally resolves today, something in that index-arithmetic path returns a
result set that gets filtered to empty before the final `series.loc[start_index:end_index]` slice —
with no exception raised anywhere in the call chain (confirmed via `logging.DEBUG` on `qlib.data`: no
"Loading expression error" is ever logged, so `_load_internal` genuinely returns empty, it isn't
throwing and getting swallowed).

**Blast radius:** every one of Qlib's built-in factor sets (Alpha158, Alpha360) and most technical
indicators are built from `Ref`, `Mean`, `Std`, `Corr`, `Rank`, etc. Assume all of them are affected
until proven otherwise. Plain field access (`$close`, `$volume`, `$open`, ...) is unaffected.

**Do NOT attempt to fix by downgrading pandas.** Tried: `pandas==2.1.4` forces pip to downgrade numpy
to 1.26.4 to satisfy pandas' own constraints, which then breaks `scipy>=1.18` (requires numpy>=2.0),
which breaks `qlib/data/ops.py`'s own `from scipy.stats import percentileofscore` import. There is no
clean pin across the currently-resolvable dependency graph.

**Workarounds, in order of preference:**
1. Don't use Qlib's expression engine for factor computation. Pull raw fields (`$close`, `$volume`, ...)
   via `D.features()` and compute rolling/derived features in Polars or plain pandas in our own code.
   This is the current plan (see root `README.md`, Agent 7 strategy).
2. If Qlib's own factor sets are needed later, root-cause the exact break point in `LocalExpressionProvider`
   / the Cython storage backend (`qlib/data/storage/`) and patch it in our fork. Not yet done — flagged
   as a spike if we decide we need it.
3. Do not pass raw `pd.Timestamp` objects directly to an `Expression.load()` call yourself when testing —
   that bypasses the time→index conversion `LocalExpressionProvider` normally does and throws a *different*,
   unrelated `TypeError` (`Addition/subtraction of integers ... with Timestamp`). This was a false lead
   during diagnosis — don't rediscover it and think it's the real bug.

**Benchmark calc is affected too:** `qlib.backtest.backtest()`'s benchmark argument, when passed a ticker
string, internally evaluates `$close/Ref($close,1)-1` — so it silently fails the same way
("`ValueError: The benchmark [...] does not exist`" is what you'll actually see, which is a red herring;
the ticker exists, its `Ref()`-based return calc doesn't). Workaround: compute the benchmark return
yourself in plain pandas and pass a pre-built `pd.Series` as `benchmark=` — `_cal_benchmark` in
`qlib/backtest/report.py` accepts a `pd.Series` directly and skips its own broken expression call.

## 2. The free US sample dataset is stale

`python scripts/get_data.py qlib_data --region us` downloads a dataset whose calendar
(`calendars/day.txt`) stops at **2020-11-10**. Any backtest/query with `end_time` after that raises
`IndexError: start_time uses a future date`. Not a bug — just old public sample data. Use date ranges
inside `[1999-12-31, 2020-11-10]` for any spike/test against this dataset, or source fresher data before
relying on results past that date.

`SPY` is listed as a valid instrument (`D.list_instruments()` includes it) but has **no actual price
data** in this sample set — `D.features(["SPY"], ...)` returns empty. Use a ticker confirmed to have
data (e.g. `AAPL`) for anything that needs a working benchmark/price series during testing.

## 3. Backtest engine is fine — but ALWAYS guard your entry point with `if __name__ == "__main__":`

A minimal `TopkDropoutStrategy` backtest (10 tickers, 108 trading days, `SimulatorExecutor`) initially
appeared to hang for 15+ minutes consuming almost no CPU. **This was not a Qlib bug.** Qlib uses
`multiprocessing` internally (visible in tracebacks referencing `multiprocessing/pool.py`). A bare
top-level test script with no `if __name__ == "__main__":` guard, run under macOS's default **spawn**
multiprocessing start method, causes every spawned worker to re-import and re-execute the entire
script from scratch — which re-triggers the same multiprocessing call, in an unbounded loop of
`RuntimeError: An attempt has been made to start a new process before the current process has finished
its bootstrapping phase`. That loop is what consumed 15 minutes of wall-clock time for no result.

**Fix:** wrap the script's logic in `def main(): ...` and call it only under
`if __name__ == "__main__": main()`. With that fix, the exact same backtest completed in **~7 seconds**
(108 steps, ~925 it/s) and produced a correct equity curve. **Any script — not just backtests — that
imports `qlib` and might be run directly (not just imported as a module) needs this guard on macOS.**

## Environment note (unrelated to the above, but adjacent)

The host's system Python was 3.14 — too new for `pyqlib` (wheels only published up to cp312, it's an
Alpha-status Cython package). Fixed by `brew install python@3.12` (does not touch system Python) and
building the project `.venv` on `/opt/homebrew/bin/python3.12`. If `.venv` is ever recreated, recreate
it from `python3.12`, not the system `python3`.
