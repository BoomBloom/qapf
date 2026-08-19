from pydantic import BaseModel, Field


class CodeGenRequest(BaseModel):
    """What to implement, specified the way a real request would arrive:
    natural-language spec (from a paper/pseudocode, per README's roster call
    for this agent) plus an executable definition of "correct" — this agent
    never grades its own homework."""

    spec: str = Field(description="Natural-language description of the algorithm to implement.")
    function_signature: str = Field(description="Exact `def name(...) -> ...:` line the generated code must match.")
    verification_script: str = Field(
        description="Python source that imports the generated function from `solution` and asserts "
        "correctness independently. Must exit 0 on success, non-zero (an uncaught exception/assert) "
        "on failure — that exit code is the only signal this agent trusts."
    )


class GenerationAttempt(BaseModel):
    attempt_n: int
    provider: str
    model: str
    code: str | None = Field(description="Extracted Python source, or None if extraction itself failed.")
    passed: bool
    error: str | None = Field(description="Captured stderr/traceback from running the verification script.")


class GeneratedCode(BaseModel):
    function_signature: str
    final_code: str | None
    all_tests_passed: bool
    attempts: list[GenerationAttempt]
    reasoning: list[str]
