from pydantic import BaseModel, Field


class SolverResult(BaseModel):
    """One solver's answer to the identical cardinality-constrained subset
    selection problem — same tickers, same objective, same k."""

    method: str
    selected: list[str]
    objective_value: float
    feasible: bool = Field(description="Selected exactly k names, no more, no fewer.")
    wall_clock_seconds: float


class QuantumSelectionResult(BaseModel):
    """QAOA's result plus two independent classical references it's checked
    against — never reported alone, per README's own "Scope warning" that
    QAOA is not expected to beat classical solvers here."""

    universe: list[str]
    k: int
    risk_aversion: float

    brute_force: SolverResult = Field(description="Ground truth: exhaustive search over the exact constrained problem, no QUBO penalty involved.")
    exact_qubo: SolverResult = Field(description="NumPyMinimumEigensolver's exact ground state of the SAME QUBO encoding QAOA runs on — isolates QUBO-encoding correctness from QAOA's approximation quality.")
    qaoa: SolverResult

    qaoa_matches_brute_force: bool
    qaoa_matches_exact_qubo: bool
    qaoa_objective_gap_pct: float = Field(description="How much worse QAOA's objective is than the true optimum, in percent. 0.0 = found the optimum.")
    reasoning: list[str]
