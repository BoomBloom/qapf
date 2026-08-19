"""LLM provider wiring for Agent 1.

Two tiers, per the operator's explicit cost-discipline decision (wayfinder
"complete the rest of agents" grill, 2026-08-19): Groq for every frequent,
per-node call ("quick-thinking" — free/near-free, fast), Anthropic reserved
for the single deep-thinking CIO synthesis call per pipeline run, not every
node. Matches the operator's standing instruction not to overuse the paid
Claude key.

Reuses `tradingagents.llm_clients.create_llm_client` directly rather than
reimplementing a provider factory — this is exactly what README.md's roster
calls "directly reusable" for Agent 1 (Apache-2.0, TradingAgents). Importing
`tradingagents` also runs its own `load_dotenv(find_dotenv(usecwd=True))`
(see reference/TradingAgents/tradingagents/__init__.py), which is what
actually makes the .env-stored keys visible to this process — no separate
dotenv call needed here.
"""

import tradingagents  # noqa: F401  (import side effect: loads .env via find_dotenv)
from tradingagents.llm_clients import create_llm_client

# Verified live 2026-08-19 against Groq's actual /v1/models endpoint --
# llama-3.3-70b-versatile (the obvious guess) came back 404, decommissioned.
# openai/gpt-oss-120b was confirmed present in that same live listing and is
# Groq's largest general-purpose open-weight model, a reasonable
# quick-thinking default for code generation (Agent 8) specifically. Re-check
# the live model list if this ever 404s again -- Groq's catalog turns over.
QUICK_MODEL = "openai/gpt-oss-120b"

# claude-sonnet-5: "near-frontier intelligence at Sonnet cost" per
# tradingagents' own model catalog description -- the cheapest Anthropic tier
# still worth using for a once-per-run synthesis call, not the more expensive
# Opus/Fable options also available.
DEEP_MODEL = "claude-sonnet-5"


def get_quick_llm(temperature: float = 0.1):
    """Cheap, fast LLM for frequent per-node calls. Currently only used by
    tests/spot-checks in this module -- the pipeline itself has no per-node
    LLM calls (see state_graph.py's docstring for why), but is kept available
    for any future node that needs one, per the operator's tier decision."""
    return create_llm_client(
        provider="groq", model=QUICK_MODEL, temperature=temperature
    ).get_llm()


def get_deep_llm():
    """The single paid-Anthropic call per pipeline run: the CIO's final
    decision synthesis in state_graph.py's `cio_synthesis` node.

    No `temperature` kwarg -- verified live (2026-08-19) that claude-sonnet-5
    rejects it outright ("`temperature` is deprecated for this model"), unlike
    the Groq-hosted quick tier. Newer Claude models fix their sampling
    internally rather than exposing it as a caller knob."""
    return create_llm_client(provider="anthropic", model=DEEP_MODEL).get_llm()
