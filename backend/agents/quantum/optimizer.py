"""Agent 5 — Quantum & Optimization.

Built last and deliberately scoped narrow, matching README's own "Scope
warning": *"QAOA/QUBO on today's simulators does not beat classical solvers
for portfolio problems of realistic size... keep it as a research curiosity,
not a critical path item."* This agent exists to VERIFY that claim against
this project's own real data, not to replace Agent 2's portfolio construction
-- if QAOA ever did start winning on some future problem shape, that would be
a real, notable finding, and this agent is what would catch it. It never
reports a QAOA result alone; every run is checked against two independent
classical references (see schemas.SolverResult) before anything is trusted.

THE PROBLEM. Not the same one Agent 2 solves. Agent 2 takes an already-signed
universe and finds continuous weights (cvxpy, Ledoit-Wolf shrinkage
covariance). This agent asks a genuinely different, discrete question: given
Agent 7's signals and Agent 2's own covariance estimate, WHICH k of n
candidate names should even be in the portfolio, evaluated on the same
risk-return tradeoff Agent 2 optimizes for. That's a combinatorial
(cardinality-constrained subset selection) problem -- the shape QUBO/QAOA
formulations are actually built for, unlike continuous weight allocation.

  minimize   risk_aversion * sum_{i,j in S} Sigma[i,j]  -  sum_{i in S} mu[i]
  subject to |S| = k

encoded as a QUBO with a quadratic penalty enforcing the cardinality
constraint softly:

  g(x) = risk_aversion * x^T Sigma x  -  mu^T x  +  penalty * (sum(x) - k)^2

WHY THE UNIVERSE IS TRIMMED. QAOA on a local simulator scales badly with
qubit count -- this is itself part of the "not a critical path item" finding,
not an artificial handicap. `select_subset` trims to the top `max_candidates`
names by |signal| before building the QUBO, and documents the trim in
`reasoning` rather than silently shrinking the problem.
"""

import logging
import time

import numpy as np
import pandas as pd
from itertools import combinations

from qiskit.primitives import StatevectorSampler
from qiskit_algorithms import QAOA, NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import COBYLA
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer

from .schemas import QuantumSelectionResult, SolverResult

logger = logging.getLogger(__name__)


class QuantumPortfolioOptimizer:
    def __init__(self, reps: int = 2, maxiter: int = 100, seed: int = 42, max_candidates: int = 10):
        self.reps = reps
        self.maxiter = maxiter
        self.seed = seed
        self.max_candidates = max_candidates

    def _build_qubo(self, tickers: list[str], mu: np.ndarray, sigma: np.ndarray, k: int) -> tuple[QuadraticProgram, float]:
        n = len(tickers)
        # Heuristic but generous: must dominate the largest possible change in
        # the unconstrained terms from adding/removing one variable, or an
        # infeasible solution could beat the true optimum.
        penalty = 10.0 * (self.risk_aversion * float(np.abs(sigma).max()) * n + float(np.abs(mu).max()))

        qp = QuadraticProgram()
        for t in tickers:
            qp.binary_var(t)

        linear = {t: -float(mu[i]) - 2 * penalty * k for i, t in enumerate(tickers)}
        quadratic = {}
        for i, ti in enumerate(tickers):
            quadratic[(ti, ti)] = self.risk_aversion * float(sigma[i, i]) + penalty
            for j in range(i + 1, n):
                tj = tickers[j]
                quadratic[(ti, tj)] = self.risk_aversion * float(sigma[i, j] + sigma[j, i]) + 2 * penalty

        qp.minimize(linear=linear, quadratic=quadratic)
        return qp, penalty

    def _true_objective(self, selected_idx: list[int], mu: np.ndarray, sigma: np.ndarray) -> float:
        """The REAL constrained objective (no penalty term) -- what brute
        force optimizes directly and what every solver is ultimately judged
        against."""
        if not selected_idx:
            return 0.0
        sub_sigma = sigma[np.ix_(selected_idx, selected_idx)]
        return float(self.risk_aversion * sub_sigma.sum() - mu[selected_idx].sum())

    def _brute_force(self, tickers: list[str], mu: np.ndarray, sigma: np.ndarray, k: int) -> SolverResult:
        """Ground truth: exhaustive search over every valid k-subset,
        independent of the QUBO encoding entirely -- catches a QUBO-encoding
        bug that both NumPyMinimumEigensolver and QAOA would share, since
        neither is used here."""
        start = time.perf_counter()
        n = len(tickers)
        best_obj, best_idx = np.inf, None
        for combo in combinations(range(n), k):
            obj = self._true_objective(list(combo), mu, sigma)
            if obj < best_obj:
                best_obj, best_idx = obj, combo
        elapsed = time.perf_counter() - start
        return SolverResult(
            method="brute_force",
            selected=[tickers[i] for i in best_idx],
            objective_value=best_obj,
            feasible=True,
            wall_clock_seconds=elapsed,
        )

    def _exact_qubo(self, qp: QuadraticProgram, tickers: list[str], mu: np.ndarray, sigma: np.ndarray, k: int) -> SolverResult:
        """Exact ground state of the SAME QUBO QAOA runs on -- isolates
        "did QAOA approximate correctly" from "is the QUBO encoding itself
        correct" (that's what _brute_force checks instead)."""
        start = time.perf_counter()
        result = MinimumEigenOptimizer(NumPyMinimumEigensolver()).solve(qp)
        elapsed = time.perf_counter() - start
        selected_idx = [i for i, v in enumerate(result.x) if round(v) == 1]
        return SolverResult(
            method="exact_qubo",
            selected=[tickers[i] for i in selected_idx],
            objective_value=self._true_objective(selected_idx, mu, sigma),
            feasible=len(selected_idx) == k,
            wall_clock_seconds=elapsed,
        )

    def _qaoa(self, qp: QuadraticProgram, tickers: list[str], mu: np.ndarray, sigma: np.ndarray, k: int) -> SolverResult:
        start = time.perf_counter()
        qaoa = QAOA(
            sampler=StatevectorSampler(),
            optimizer=COBYLA(maxiter=self.maxiter),
            reps=self.reps,
        )
        result = MinimumEigenOptimizer(qaoa).solve(qp)
        elapsed = time.perf_counter() - start
        selected_idx = [i for i, v in enumerate(result.x) if round(v) == 1]
        return SolverResult(
            method="qaoa",
            selected=[tickers[i] for i in selected_idx],
            objective_value=self._true_objective(selected_idx, mu, sigma),
            feasible=len(selected_idx) == k,
            wall_clock_seconds=elapsed,
        )

    def select_subset(
        self,
        candidate_signals: dict[str, float],
        covariance: pd.DataFrame,
        k: int,
        risk_aversion: float = 0.5,
    ) -> QuantumSelectionResult:
        self.risk_aversion = risk_aversion
        reasoning: list[str] = []

        all_tickers = sorted(candidate_signals, key=lambda t: -abs(candidate_signals[t]))
        tickers = all_tickers[: self.max_candidates]
        if len(all_tickers) > self.max_candidates:
            reasoning.append(
                f"Trimmed {len(all_tickers)} candidates to the top {self.max_candidates} by |signal| -- "
                f"QAOA on a local simulator scales badly with qubit count; this is itself part of what "
                f"README's Scope warning means by 'not a critical path item,' not an artificial handicap."
            )
        if k >= len(tickers):
            raise ValueError(f"k={k} must be smaller than the candidate pool ({len(tickers)})")

        mu = np.array([candidate_signals[t] for t in tickers])
        sigma = covariance.loc[tickers, tickers].to_numpy()

        qp, penalty = self._build_qubo(tickers, mu, sigma, k)
        reasoning.append(f"QUBO built: {len(tickers)} binary variables, cardinality penalty={penalty:.4f}.")

        bf = self._brute_force(tickers, mu, sigma, k)
        eq = self._exact_qubo(qp, tickers, mu, sigma, k)
        qa = self._qaoa(qp, tickers, mu, sigma, k)

        matches_bf = set(qa.selected) == set(bf.selected) and qa.feasible
        matches_eq = set(qa.selected) == set(eq.selected) and qa.feasible
        gap_pct = (
            0.0 if bf.objective_value == 0 or not qa.feasible
            else float((qa.objective_value - bf.objective_value) / abs(bf.objective_value) * 100)
        )

        reasoning.append(
            f"QAOA {'matched' if matches_bf else 'did NOT match'} the true (brute-force) optimum."
        )
        reasoning.append(
            f"QAOA {'matched' if matches_eq else 'did NOT match'} the exact QUBO ground state "
            f"(NumPyMinimumEigensolver) -- isolates approximation error from encoding error."
        )
        if not qa.feasible:
            reasoning.append(
                f"QAOA returned an INFEASIBLE selection ({len(qa.selected)} names, wanted {k}) -- "
                f"the soft cardinality penalty wasn't enough to force a clean k-subset this run."
            )
        reasoning.append(
            f"Wall clock: brute_force={bf.wall_clock_seconds:.4f}s, exact_qubo={eq.wall_clock_seconds:.4f}s, "
            f"qaoa={qa.wall_clock_seconds:.4f}s."
        )
        if not matches_bf:
            reasoning.append(
                f"Consistent with README's Scope warning: QAOA on today's simulators is not expected to "
                f"beat classical solvers at this problem size. This run is evidence, not a surprise."
            )

        return QuantumSelectionResult(
            universe=tickers, k=k, risk_aversion=risk_aversion,
            brute_force=bf, exact_qubo=eq, qaoa=qa,
            qaoa_matches_brute_force=matches_bf, qaoa_matches_exact_qubo=matches_eq,
            qaoa_objective_gap_pct=gap_pct, reasoning=reasoning,
        )
