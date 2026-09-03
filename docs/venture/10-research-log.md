# Research Log

Append-only. Every entry: date, question, finding, source, and confidence. Never re-research
a question that has an entry here — extend the entry instead.

Confidence scale: **verified** (read primary source / ran it) · **reported** (secondary
source, plausible) · **unverified** (claim encountered, not checked)

---

## §0 — 2026-08-27 · ENVIRONMENT CONSTRAINT (read this before trusting any confidence tag)

This cloud session's egress proxy denies CONNECT to essentially every primary research
source with a **403 policy denial** — not a network error, an organizational allow-list.
Confirmed at the proxy status endpoint, not merely inferred from failed fetches.

Blocked and confirmed: `ssrn.com`, `semanticscholar.org`, `researchgate.net`,
`academic.oup.com`, `arxiv.org`, `mdpi.com`, `www.sec.gov`, `www.federalreserve.gov`,
`www.nasdaq.com`, `www.spglobal.com`, `www.morningstar.com`, `quantpedia.com`,
`jacobslevycenter.wharton.upenn.edu`, `www.bogleheads.org`, plus the market-data APIs
`api.binance.com`, `fapi.binance.com`, `api.kraken.com`, `api.coingecko.com`,
`api.hyperliquid.xyz`, `www.alphavantage.co`.

Reachable: WebSearch (result summaries), github.com, pypi.org, npm.

### What this means
1. **Every Phase 1 finding is `[reported]` at best.** No primary paper was read; no live
   funding rate, fee schedule, or filing was fetched. Treat the research files as a
   well-sourced *hypothesis generator*, not as verified fact.
2. **Before any thesis drives architecture, its primary sources must be re-verified from a
   machine with open network access** (i.e. the local Claude Code session, not this one).
3. **The kill tests are unaffected.** Falsification runs on price data held locally — it
   never needed the web. This is the strongest argument for killing theses empirically
   rather than adjudicating them from literature.

Per the proxy README, policy denials must be reported rather than routed around. No attempt
was made to circumvent them.

---

## §1 — 2026-08-27 · Is there open-source quantum computing for trading, and does it work?

**Question:** Does open-source quantum software for trading exist, and does quantum hardware
currently beat classical methods on portfolio problems?

### The software exists and is free

| Project | License / owner | Status (Aug 2026) | Confidence |
|---|---|---|---|
| `qiskit-finance` | Apache 2.0, `qiskit-community` | Alive but **community-maintained** — IBM handed it off. 316 commits, 7 open issues. Ships a `PortfolioOptimization` application class and data providers. | verified (repo page) |
| `qiskit-optimization` | Apache 2.0, `qiskit-community` | **"No longer officially supported by IBM"**; maintainership passed to Quantagonia; users directed to `qiskit-addon-opt-mapper`. | reported |
| `qiskit-machine-learning` | Apache 2.0, `qiskit-community` | Maintained by STFC Hartree Centre. Quantum kernels, QNNs, classifiers/regressors. | reported |
| PennyLane | Apache 2.0, Xanadu | Actively maintained; the strongest option for *differentiable* hybrid quantum-classical models. Has a Qiskit plugin. | reported |
| D-Wave Ocean SDK | Apache 2.0, D-Wave | Open source; annealing-oriented (QUBO/Ising). The most production-adjacent quantum optimization path. | reported |

Real QPU access is also obtainable free at small scale (IBM Quantum open plan, D-Wave Leap
trial). **Access is not the bottleneck.**

### The performance does not

- Benchmarks against classical baselines (MIP, simulated annealing, tabu search, steepest
  descent, tailored heuristics) found **QAOA and quantum annealing were outperformed by
  classical heuristics within a 60-second time limit** on real-world instances. [reported]
- QAOA converges well in *noiseless* simulation but **degrades with problem size** because
  transpilation demands rapidly increasing SWAP-gate counts. [reported]
- Standard QAOA **failed** on S&P 100 / Nikkei 225-scale instances; hybrid quantum-classical
  algorithms solved them substantially more often. [reported]
- Pro-quantum result worth noting *and distrusting*: a 10-equity basket backtested over 2025
  reported QAOA Sharpe **1.81** vs simulated annealing 1.31 vs HRP 0.98. Ten assets, one
  year, one market regime — far too small to establish anything. [unverified]

### Independent confirmation from our own code

QAPF's Agent 5 (`backend/agents/quantum/`) already ran cardinality-constrained subset
selection via QAOA against brute-force enumeration and `NumPyMinimumEigensolver`. It found
the correct answer and took **~13,000× longer** than brute force on a 6-name problem.
[verified — our own run]

**Conclusion:** the open-source quantum stack is real, free, and usable. Quantum *hardware
advantage* for portfolio optimization does not exist at tradable scale in 2026. Anyone
selling "quantum trading returns" today is selling the word, not the math.

### The quantum-inspired exception

Tensor-network and QUBO methods running on **classical** hardware are a different story:
they handle structured high-dimensional problems (portfolio optimization demonstrated at
~1272 fully-connected variables) and are in commercial production — Multiverse Computing has
raised $344M+ selling exactly this to financial institutions. Sources caution that adoption
should go through "benchmarked pilots against strong classical baselines rather than generic
claims of exponential compression." [reported]

**This is the only branch of "quantum" with a defensible near-term claim on real money.**

### Sources
- https://github.com/qiskit-community/qiskit-finance
- https://medium.com/qiskit/a-new-chapter-for-qiskit-algorithms-and-applications-5baff541e826
- https://arxiv.org/pdf/2509.17876 — *Quantum Portfolio Optimization: An Extensive Benchmark*
- https://arxiv.org/pdf/2603.13607 — *The Quest for Quantum Advantage in Combinatorial Optimization*
- https://arxiv.org/html/2602.14827v1 — *Constrained Portfolio Optimization via QAOA with XY-Mixers*
- https://doi.org/10.3390/e28080916 — *Benchmarking Quantum Solvers in Noisy Digital Simulations*
- https://arxiv.org/html/2404.11277v2 — *Quantum-inspired Techniques in Tensor Networks for Industrial Contexts*
- https://www.sciencenews.org/investors-lab/the-quantum-bargain
- https://link.aps.org/doi/10.1103/PhysRevResearch.4.013006 — *Dynamic portfolio optimization ... tensor networks*

> Note: arxiv.org, mdpi.com and thequantuminsider.com are blocked by this session's egress
> proxy. Findings marked *reported* come from search-result summaries, not the primary PDFs.
> **Read the primaries before betting architecture on them.**

---

## §2 — pending: where does a retail-scale edge actually still exist?

Not yet researched. This is Phase 1 of the plan and must produce falsifiable candidate
theses with kill tests, not a survey of strategy families.
