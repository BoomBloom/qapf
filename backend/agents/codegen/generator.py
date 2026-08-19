"""Agent 8 — Quantitative Software Engineering (Code Generation).

"paper/pseudocode -> tested Python" (README.md's roster line). The defining
design choice: this agent never trusts its own output. Every attempt is
actually EXECUTED against a verification script the caller supplies (not
written or graded by the same model that wrote the code), in a subprocess
with a timeout — matching this project's standing rule that a claim (here,
"this code is correct") gets checked against real execution, not asserted.

Cost discipline (the operator's explicit tier decision, 2026-08-19, applied
identically to Agent 1): Groq (quick, near-free) gets two attempts first.
Anthropic (deep, real cost per call) is only invoked on a third attempt, and
only if both Groq attempts failed — escalate to the paid model when the cheap
one struggles, not by default.

Subprocess, not exec() in-process: LLM-generated code runs in a fresh
`python` subprocess with a hard timeout, not `exec()`'d into this agent's own
process. A runaway or malformed snippet (infinite loop, resource exhaustion)
can only take down its own subprocess, not this one -- proportionate
isolation for a single-operator local tool generating its own utility code,
not a claim of a full sandbox.
"""

import logging
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from core.config import DEEP_MODEL, QUICK_MODEL, get_deep_llm, get_quick_llm

from .schemas import CodeGenRequest, GenerationAttempt, GeneratedCode

logger = logging.getLogger(__name__)

VERIFICATION_TIMEOUT_SECONDS = 15
MAX_QUICK_ATTEMPTS = 2

_CODE_BLOCK_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def _extract_code(response_text: str) -> str | None:
    """Pull the first fenced Python block out of an LLM response. Returns
    None (not the raw response) when no fenced block is found -- generated
    code is only ever code we can point to, never a guess at what a
    prose-wrapped response "probably" meant."""
    match = _CODE_BLOCK_RE.search(response_text)
    if match:
        return match.group(1).strip()
    return None


def _run_verification(code: str, verification_script: str) -> tuple[bool, str | None]:
    """Write the generated function to solution.py and the caller's
    verification script alongside it in a fresh temp dir, run the
    verification script as a subprocess, and trust only its exit code."""
    with tempfile.TemporaryDirectory(prefix="qapf_codegen_") as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "solution.py").write_text(code)
        verify_path = tmp_path / "verify.py"
        verify_path.write_text(verification_script)

        try:
            result = subprocess.run(
                [sys.executable, str(verify_path)],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=VERIFICATION_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return False, f"Verification script did not finish within {VERIFICATION_TIMEOUT_SECONDS}s (possible infinite loop)."

        if result.returncode == 0:
            return True, None
        return False, (result.stderr or result.stdout or f"Non-zero exit ({result.returncode}), no output captured.").strip()


class CodeGenAgent:
    def generate(self, request: CodeGenRequest) -> GeneratedCode:
        reasoning: list[str] = []
        attempts: list[GenerationAttempt] = []
        prior_error: str | None = None
        prior_code: str | None = None

        for attempt_n in range(1, MAX_QUICK_ATTEMPTS + 2):  # 2 quick + 1 deep
            use_deep = attempt_n > MAX_QUICK_ATTEMPTS
            llm = get_deep_llm() if use_deep else get_quick_llm()
            provider = "anthropic" if use_deep else "groq"
            model = DEEP_MODEL if use_deep else QUICK_MODEL

            if use_deep and attempt_n == MAX_QUICK_ATTEMPTS + 1:
                reasoning.append(
                    f"Escalating to Anthropic after {MAX_QUICK_ATTEMPTS} failed Groq attempt(s) — "
                    f"per the operator's cost-tier decision, the paid model is used only when the "
                    f"free tier couldn't produce passing code."
                )

            prompt = self._build_prompt(request, prior_code, prior_error)
            response = llm.invoke(prompt)
            response_text = response.content if hasattr(response, "content") else str(response)
            code = _extract_code(response_text)

            if code is None:
                error = "No fenced Python code block found in the model's response."
                attempts.append(GenerationAttempt(
                    attempt_n=attempt_n, provider=provider, model=model,
                    code=None, passed=False, error=error,
                ))
                prior_error, prior_code = error, None
                logger.warning("codegen attempt %d (%s): %s", attempt_n, provider, error)
                continue

            passed, error = _run_verification(code, request.verification_script)
            attempts.append(GenerationAttempt(
                attempt_n=attempt_n, provider=provider, model=model,
                code=code, passed=passed, error=error,
            ))
            logger.info("codegen attempt %d (%s): %s", attempt_n, provider, "PASSED" if passed else "FAILED")

            if passed:
                reasoning.append(f"Attempt {attempt_n} ({provider}/{model}) passed verification.")
                return GeneratedCode(
                    function_signature=request.function_signature,
                    final_code=code, all_tests_passed=True,
                    attempts=attempts, reasoning=reasoning,
                )
            prior_error, prior_code = error, code

        reasoning.append(
            f"All {len(attempts)} attempt(s) failed verification, including the Anthropic escalation. "
            f"Returning no code rather than a plausible-looking but unverified implementation."
        )
        return GeneratedCode(
            function_signature=request.function_signature,
            final_code=None, all_tests_passed=False,
            attempts=attempts, reasoning=reasoning,
        )

    def _build_prompt(self, request: CodeGenRequest, prior_code: str | None, prior_error: str | None) -> str:
        parts = [
            "Implement the following algorithm in Python. Respond with ONLY a single "
            "fenced ```python code block containing a complete, self-contained "
            "implementation -- no prose outside the fence, no example usage, no "
            "if __name__ == '__main__' block.",
            f"\nSpecification:\n{request.spec}",
            f"\nRequired function signature (match exactly, including the module-level "
            f"import of anything the signature's type hints need):\n{request.function_signature}",
        ]
        if prior_code and prior_error:
            parts.append(
                f"\nA previous attempt failed verification. Previous code:\n```python\n{prior_code}\n```"
                f"\nVerification error:\n{prior_error}\nFix the specific problem shown above."
            )
        return "\n".join(parts)
