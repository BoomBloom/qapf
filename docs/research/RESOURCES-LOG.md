# Resources log

Every resource the operator has sent, in the order sent, with status. Kept so nothing gets lost across a
long session and nothing gets silently re-checked twice. Update this file every time a new resource
arrives or a status changes — don't let it drift out of sync with reality.

**Legend:** ✅ checked & applied · 🔍 checked, no action needed · ❌ rejected (with reason) · ⏳ pending
(not yet checked) · 💥 dispatched but failed before producing findings · 🚫 cannot access (video/paywall)

---

## Batch 0 — early AI-generated blueprints (pre-wayfinder)

| Resource | Status | Verdict |
|---|---|---|
| DeepSeek architecture doc | 🔍 | Restated the same 12-agent design, no new verification. One structural detail (core/api/models/services split) merged into README. |
| Qwen Studio text | 🔍 | Same as above. |
| "AI Agents for Prop Trading.md" | 🔍 | Same as above. |

## Batch 1 — quant methodology (PDFs + book list)

| Resource | Status | Verdict |
|---|---|---|
| Kakushadze & Serur, "151 Estrategias de Trading" (arXiv 1912.04492) | 💥 | Fed into the "viable alpha families" research agent — **that agent failed on session limit before producing findings.** Not yet actually used. |
| *Machine Learning for Algorithmic Trading* (Jansen) | 💥 | Same prompt, same failure. Not yet checked. |
| *Systematic Trading* (Carver) | 💥 | Fed into both the alpha-families AND position-sizing prompts — **both failed.** Not yet checked. |
| *Trading Systems and Methods* (Kaufman) | 💥 | Same as above, not yet checked. |
| *Advances in Financial Machine Learning* (López de Prado) | 💥 | Fed into alpha-families prompt — failed. Not yet checked (Agent 4 already implements his/Bailey's Deflated Sharpe Ratio independently, from prior knowledge, not this book). |
| *The Leverage Space Trading Model* (Vince) | 💥 | Fed into position-sizing prompt — failed. Not yet checked. |
| *The Mathematics of Money Management* (Vince) | 💥 | Same as above. |
| *Algorithmic Short Selling with Python* (Bernut) | 💥 | Fed into alpha-families prompt — failed. Relevant given the book is long-only. |
| *Differential Geometry and Statistics* (PDF) | ⏳ | Deliberately deprioritized — genuinely Agent 4's domain, but not urgent while the strategy can't clear a basic validation bar. |
| *B18842_HFT_eBook* (PDF) | ⏳ | Deprioritized — daily rebalance, not intraday; would inform Agent 11's cost model, not urgent. |

**⚠️ ACTION NEEDED: re-dispatch the alpha-families and position-sizing research once the session limit
resets. Both were fully specified and ready; they simply never ran to completion.**

## Batch 2 — links (tools, papers, courses)

| Resource | Status | Verdict |
|---|---|---|
| quantpad.ai | ❌ | Closed SaaS, PineScript/NinjaScript, targets prop-firm challenge evaluation (already ruled incompatible). |
| TabPFN (github + colab demo) | ❌ | Rejected as a return predictor — license (best checkpoint is non-commercial), zero peer-reviewed evidence on equity returns, and its own paper admits it struggles extrapolating past its conditioning set. One narrow trial allowed: v2 weights (Apache-2.0) for *regime classification*, not return prediction. See `docs/research/data-and-modelling-tooling.md`. |
| Lindemann, Dunis & Lisboa (2005), GMM regime paper (tandfonline) | ⏳ | Identified (title/authors/journal confirmed via Crossref) — directly matches Agent 4's deliberately-deferred "regime-switching... not built" scope. Not yet read in full or applied. |
| end-to-end-machine-learning (Teachable course) | ⏳ | Deprioritized, too diffuse without a specific question. |
| ConvTimeNet (arXiv 2403.01493) | ⏳ | Identified (title/authors confirmed) — candidate signal-generation architecture for Agent 7. Not yet read in full or applied. |
| ml-quant.com/archive | ⏳ | Deprioritized, too diffuse. |
| OpenBB-finance/OpenBB | ❌ | Rejected as a data fix — AGPL-3.0 (license conflict), no delisted-security data anywhere in 2,710 files, sells no data of its own. **Byproduct: led to discovering `reference/qlib`'s own free point-in-time constituents builder**, which is now the actual plan for tickets 03/10. See `docs/research/data-and-modelling-tooling.md`. |
| cantaro86/Financial-Models-Numerical-Methods | 💥 | Fed into the failed alpha-families prompt. Not yet checked directly. |
| 5x YouTube videos (algo trading) | 🚫 | Cannot watch video. Tell me what's in one if it matters and I'll act on the specific claim. |
| paperswithbacktest/awesome-systematic-trading | 🔍 | Verified real (13,510 stars) but last pushed 2025-01-22, ~7 months stale. Curated index — best used as a pointer for a specific need, not read cover to cover. See `docs/research/vibe-trading-and-community-resources.md`. |
| HKUDS/Vibe-Trading | 🔍 | Verified real (31,276 stars, MIT, active). Genuine strengths QAPF lacks (registry-based systematic look-ahead testing, IC/IR factor diagnostics) and genuine gaps QAPF doesn't have (zero hits for deflated/sharpe/purge/monte_carlo across 2,610 files — no overfitting-correction machinery at all). Two low-priority adoption ideas logged, neither urgent. Full writeup in `docs/research/vibe-trading-and-community-resources.md`. |

## Batch 3 — Fincept / QuantConnect / Nautilus (2026-08-19)

| Resource | Status | Verdict |
|---|---|---|
| Fincept-Corporation/FinceptTerminal | ❌ | Verified AGPL-3.0 (GitHub's API showed `NOASSERTION`; the raw `LICENSE` file confirms AGPL-3.0-or-later) — same license conflict as OpenBB. C++/Qt6 desktop terminal for market data/research display, not a strategy or backtesting framework — wrong category for what this project needs from it. Real (30,390 stars, actively maintained) but not adoptable as code. Possible future use: pure visual/UX inspiration for QAPF's own dashboard, which sidesteps the license issue entirely since no code would be taken. |
| fincept.in (marketing site) | ⏳ | Not fetched — marketing copy for the above, low priority. |
| Fincept MCP integration source | ⏳ | URL was truncated by YouTube and not resolved to a specific path — ask if this matters beyond the main repo already checked. |
| Fincept "screens directory" | ⏳ | Same — truncated, not resolved. |
| Bloomberg Terminal pricing reference (wallstreetprep) | ⏳ | Not fetched — context for why Fincept exists (Bloomberg costs ~$20k+/yr), not directly actionable for QAPF. |
| modelcontextprotocol.io | 🔍 | General MCP reference; already understood, no new action. |
| QuantConnect / LEAN engine | 🔍 | Verified: LEAN itself is **Apache-2.0** (no license conflict, unlike Fincept/OpenBB), 21,266 stars, mature (created 2014), actively maintained. A legitimate, complete research+backtest+live platform. **Not adopted**: QAPF already has 10+ agents built around Qlib's backtest engine; swapping engines now would be a full rebuild with no demonstrated need. Worth remembering for ticket 09 as an alternative to self-hosting nautilus_trader — QuantConnect's hosted platform natively supports IBKR too. |
| YouTube ZVMTeDBmSrI | 🚫 | Cannot watch. Tell me what's in it if relevant. |
| nautechsystems/nautilus_trader | 🔍 | **The most directly useful new find.** Verified: LGPL-3.0 (materially different from AGPL — no network-copyleft trigger, using as a library is standard practice), 26,318 stars, mature (created 2018), Rust-core, very actively maintained. README explicitly claims and documents "research-to-live parity — identical strategy implementations between research and live deployment." **Confirmed stable Interactive Brokers integration** — directly relevant to ticket 09, where IBKR is already the leading broker candidate. Not adopted yet (no code changes made) — flagged as a serious candidate for the live/paper-trading execution layer when ticket 09 is worked, since QAPF has no live-trading path at all today and this project is specifically built to solve backtest-to-live divergence, which is exactly QAPF's next real gap after validation. |

---

## Open follow-ups this log exists to prevent losing

1. **Re-run the alpha-families and position-sizing research** (💥 above) once the session-limit window
   resets — both prompts are already written and ready, they just never completed.
2. Read the GMM regime paper and ConvTimeNet in full when Agent 4/7 improvement work is actually next in
   priority (after ticket 07's result is known).
3. nautilus_trader is now a real input to ticket 09 (broker/platform) — surface it when that ticket is
   worked, don't let it sit only in this log.
