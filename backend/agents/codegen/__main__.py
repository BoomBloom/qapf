"""Manual verification runner: python -m agents.codegen

Demonstrates Agent 8 on a real, useful, previously-unimplemented task rather
than a toy: the symmetric CUSUM filter (Lopez de Prado, "Advances in
Financial Machine Learning") -- an event-based sampling technique from one of
the resources the operator sent early in this project
(docs/research/RESOURCES-LOG.md, Batch 1) that was never actually applied
because the research-agent dispatch for it failed. QAPF has no CUSUM filter
anywhere in the codebase; this both verifies Agent 8 and closes that specific
open item.

The verification script below is an INDEPENDENT reference implementation
(hand-traced, not generated) against a hand-constructed series whose three
expected event dates were computed by tracing the textbook recursion by hand,
not by running any code -- the standard this project holds every other
correctness check to (Agents 6, 7, 9, 10 all recompute independently rather
than trusting their own output).
"""

import logging

from .generator import CodeGenAgent
from .schemas import CodeGenRequest

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

CUSUM_SPEC = """\
The symmetric CUSUM filter (event-based sampling), as used in quantitative
finance to flag points where cumulative price/return drift exceeds a
threshold since the last flagged event (Lopez de Prado, Advances in
Financial Machine Learning, ch. 2.5.2.1).

Given a time-indexed pandas Series of returns and a positive float threshold
h, maintain two running sums starting at 0.0:
    S_pos = max(0, S_pos_prev + r_t)
    S_neg = min(0, S_neg_prev + r_t)
at each step t, processing the series in index order. Whenever S_pos > h OR
S_neg < -h, record the current index as an event and reset BOTH S_pos and
S_neg to 0.0 immediately (a trigger in either direction resets both sums,
not just the one that crossed). Continue processing the rest of the series
from zero after a reset. Return the list of event timestamps (the Series
index values at which a reset was triggered), in order, as a plain Python
list.
"""

FUNCTION_SIGNATURE = "def cusum_filter(returns: pd.Series, threshold: float) -> list:"

VERIFICATION_SCRIPT = '''
import sys
import pandas as pd
from solution import cusum_filter

dates = pd.bdate_range("2024-01-02", periods=11)
returns = pd.Series(
    [0.01, 0.01, 0.01, -0.005, 0.01, 0.01, 0.01, 0.01, -0.02, -0.02, -0.02],
    index=dates,
)
threshold = 0.025

# Independently hand-traced expected events (not run, computed by hand):
#   t0: S+=0.01                    t1: S+=0.02                 t2: S+=0.03>0.025 -> EVENT, reset
#   t3: S-=-0.005                  t4: S+=0.01,S-=0             t5: S+=0.02
#   t6: S+=0.03>0.025 -> EVENT, reset
#   t7: S+=0.01                    t8: S-=-0.02                 t9: S-=-0.04<-0.025 -> EVENT, reset
#   t10: S-=-0.02 (no event, series ends)
expected = [dates[2], dates[6], dates[9]]

result = cusum_filter(returns, threshold)
result_list = list(result)

assert len(result_list) == len(expected), (
    f"expected {len(expected)} events {list(expected)}, got {len(result_list)}: {result_list}"
)
for got, want in zip(result_list, expected):
    got_ts = pd.Timestamp(got)
    assert got_ts == want, f"event mismatch: got {got_ts}, expected {want}"

# A flat (zero-return) series must never trigger -- both sums stay at 0.
flat = pd.Series([0.0] * 10, index=pd.bdate_range("2024-01-02", periods=10))
flat_result = list(cusum_filter(flat, 0.01))
assert flat_result == [], f"flat series must produce zero events, got {flat_result}"

print("All CUSUM filter checks PASSED.")
sys.exit(0)
'''


def main():
    print("=== Agent 8 (Code Generation) verification ===\n")
    print("Task: implement the symmetric CUSUM filter from a natural-language spec,\n"
          "verified against an independently hand-traced reference, not self-graded.\n")

    request = CodeGenRequest(
        spec=CUSUM_SPEC,
        function_signature=FUNCTION_SIGNATURE,
        verification_script=VERIFICATION_SCRIPT,
    )
    result = CodeGenAgent().generate(request)

    print(f"=== Result: {'ALL TESTS PASSED' if result.all_tests_passed else 'FAILED'} "
          f"after {len(result.attempts)} attempt(s) ===\n")
    for a in result.attempts:
        status = "PASS" if a.passed else "FAIL"
        print(f"  Attempt {a.attempt_n} ({a.provider}/{a.model}): {status}")
        if not a.passed and a.error:
            print(f"    error: {a.error[:300]}")
    print()
    for line in result.reasoning:
        print(f"- {line}")

    assert result.all_tests_passed, (
        "Agent 8 failed to produce passing code across all attempts, including "
        "the Anthropic escalation -- see attempt log above."
    )
    print(f"\n=== Generated code (verified) ===\n{result.final_code}")


if __name__ == "__main__":
    main()
