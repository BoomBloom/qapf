Here is a highly critical, structural review of the QAPF system.

---

### Part 1: Architecture Soundness vs. Over-Engineering (Question 1)

#### The "Agent" Theater
Calling this a "16-agent AI workforce" is marketing theater that conflicts with your stated principle of rigor. 
* If 15 out of 16 nodes are deterministic Python scripts wrapping standard libraries (Ledoit-Wolf, Qlib, FRED API, statsmodels), **they are not agents; they are functions.** 
* Wrapping deterministic, rule-based quantitative pipelines in a graph orchestration framework (`LangGraph`) and calling them "agents" adds unnecessary cognitive overhead, debugging complexity, and execution latency. 

#### The LLM Bottleneck and Vanity CIO
Only one node makes an LLM call (the final CIO memo via Anthropic). 
* **If the operator is a single human, why do you need an LLM to write a memo to you?** You wrote the code. You know the rules. If the risk engine triggers a kill-switch, a simple `sys.exit()` or a Slack/Discord webhook with a raw JSON dump of the breach metrics is safer, faster, and 100% deterministic.
* Introducing an LLM at the final step of a real-money execution pipeline introduces non-deterministic failure modes (e.g., API timeouts, rate limits, or output formatting shifts) for zero marginal quantitative utility. 

#### Verdict on Architecture
The architecture is **wildly over-engineered** for a $1,000 account, but more importantly, it is **conceptually misaligned**. You have built a classic, deterministic quantitative trading system but wrapped it in "AI Agent" packaging. 

* **To make this sound:** Strip the agent terminology. Treat this as a modular, event-driven backtesting and execution pipeline. Remove the LLM from the critical path entirely. If you want a summary, run it as an offline, asynchronous cron job *after* execution is complete and confirmed.

---

### Part 2: Why the Sharpe Ratio Has Plateaued at 0.72–0.74 (Question 2)

Your strategy has hit a hard ceiling because of fundamental portfolio construction and asset pricing constraints, not because your volatility estimators need further tuning.

```
                  TYPICAL LONG-ONLY FACTOR DRIFT
                  
      Month 0                                     Month 1 (Rebalance)
      [Rebalance] -------- (5-Day Reversal Reverts) --------> [Stale Factor Drag]
          |                                                       |
     Alpha Peak                                             Factor Decayed
```

#### 1. The 14-Name Long-Only Universe Constraint
You are trading 14 large-cap US equities. 
* **Beta Dominance:** In a long-only portfolio of 14 liquid US large-caps, your returns will be overwhelmingly dominated by the market beta ($R_m$). Over the 2008–2017 period, the S&P 500 experienced a massive bull run (post-2009). 
* **The Benchmark Hurdle:** An equal-weight (EW) portfolio of these same 14 names is a high-beta, fully invested vehicle that captures this beta premium perfectly, resulting in a high Sharpe (0.849). 
* Because you are long-only, you cannot short the market or the low-factor-score names to isolate the pure factor premiums. Your active weights are just minor tilts around a highly correlated, beta-dominated portfolio. You cannot realistically achieve significant active Sharpe (Information Ratio) under these constraints.

#### 2. The Rebalancing Frequency vs. Factor Decay Mismatch
You have a catastrophic mismatch between your factor speeds and your execution model:
* **Factor:** 5-day reversal.
* **Execution:** Monthly rebalancing.
* **The Math:** Reversal is a high-frequency, fast-decaying anomaly. The premium of a 5-day reversal signal decays to near-zero within days. By holding these positions for a month, you are holding stale, decayed signals for ~15 out of 20 trading days. The signal becomes noise, acting as a drag on your portfolio. 
* Momentum (12-1) operates on a slower horizon, but mixing it with 5-day reversal in a monthly rebalanced portfolio means your factors are actively fighting each other.

#### 3. Cross-Sectional Normalization on a Tiny N
Rank-normalizing factors to $[-1, +1]$ across $N=14$ assets is statistically weak. The difference in rank between the 7th and 8th stock is mathematically forced to look significant, even if their underlying factor values are identical to the fourth decimal place. Your signal generator is reacting to cross-sectional noise.

---

### Part 3: Blind Spots, Risks, and Over-Claimed Rigor (Question 3)

#### 1. The "Quantum-Optimization Research" Red Flag
Having an "Agent 15" dedicated to quantum-optimization research on a 14-asset, long-only portfolio is a major red flag for **research theater**.
* Quadratic Unconstrained Binary Optimization (QUBO) or quantum eigensolvers are mathematically unnecessary for $N=14$. A classical convex optimizer (like Qlib's QP solver or `CVXPY`) solves this problem to machine precision in less than 2 milliseconds.
* If you are cross-checking the quantum solver against brute-force and classical solvers *every run*, you are burning CPU cycles to confirm that your quantum approach is, at best, redundant and, at worst, less accurate due to NISQ-era noise. This belongs in an academic sandbox, not in a production execution loop.

#### 2. Deflated Sharpe Ratio (DSR) Misapplication
DSR (Bailey & López de Prado) is a powerful tool to prevent data mining, but its mathematical validity depends on strict assumptions:
* **Independence of Trials:** DSR assumes you are tracking $N$ trials from the *same* family of strategies (e.g., tweaking the lookback parameters of a single momentum indicator). 
* **The Attempt 5 Violation:** In Attempt 5, you switched from a 4-factor risk-scaled model to a *structurally distinct* absolute momentum strategy with a 200-day trend-following cash overlay. 
* Treating this as "Trial 5" in the same DSR calculation violates the assumption of a stable trial correlation matrix. You are combining apples and oranges into the trial-count penalty, which invalidates the statistical integrity of the DSR score.

```
                             DSR TRIAL DISTORTION
                             
     [Trial 1 - 4: Factor Tilts]  ======> High correlation between trials
                 vs.
     [Trial 5: Absolute Momentum] ======> Structural break in strategy class
     
     *Result:* DSR formula penalized Trial 5 using assumptions of a continuous
              search space, leading to an incorrect statistical penalty.
```

#### 3. Micro-Account Execution Realities ($1,000 Portfolio)
Trading 14 stocks with $1,000 means an average position size of **~$71 per stock**.
* **Fractional Share Execution:** To achieve your target portfolio weights (especially with volatility-managed exposure scaling), you *must* trade fractional shares. 
* **The Cost Trap:** While IBKR Lite offers $0 commissions, fractional share executions are often filled internally via principal fills, where the broker can widen the bid-ask spread. This implicit cost is rarely captured in standard Qlib backtest datasets, which assume execution at the mid-price or close.
* **Odd-Lot Dynamics:** You have zero market power; at $71 a position, you are trading odd lots. Your fills will be at the mercy of the retail queue.

#### 4. The yfinance and Qlib Survivorship Bias Loophole
You stated that you verify everything against real data to avoid survivorship bias. However:
* **yfinance** does *not* natively retain delisted tickers. If your 14-name universe consists of surviving large-caps (e.g., AAPL, MSFT, AMZN), you have **selection bias**. You are backtesting on companies that you know, ex-post, survived and flourished from 2008 to 2017. 
* Did your 2008 universe include Lehman Brothers, Bear Stearns, or Merrill Lynch? If not, your backtest is structurally compromised, and your DSR is over-inflated regardless of the trial penalty.

---

### Part 4: Strategic Recommendations

If you want to transition this from an academic exercise to a viable real-money system, you should make these changes:

#### 1. Refactor the Universe and Portfolio Structure
* **Expand the Universe:** Increase $N$ to at least 100 stocks. This makes cross-sectional ranking statistically meaningful and reduces idiosyncratic stock risk.
* **Isolate Factors (Long-Short):** If you want to trade factors (Momentum, Reversal, Volatility), you must run a dollar-neutral long-short portfolio. Short the bottom decile and long the top decile to strip away the market beta that is currently capping your relative performance.
* **Match Factor Speed to Rebalance Speed:** If you insist on monthly rebalancing, **drop the 5-day reversal factor entirely**. Focus on intermediate momentum (3 to 12 months) and fundamental/quality factors that decay slowly.

#### 2. De-Agentize the Architecture
Reduce your architecture to three clean, deterministic pipelines:

```
[ Data Ingestion & Health ] ──> [ Quantitative Pipeline ] ──> [ Execution Engine ]
    - FRED API (Macro)              - Factor Calc (Polars)         - Hard Risk Gate
    - Exchange Data (EOD)           - Portfolio Opt (CVXPY)        - IBKR API (Fix/REST)
```

Keep the Anthropic LLM completely out of the execution loop. Use it only for post-trade analysis and generating weekend performance reports.

#### 3. Retire the "Quantum" and "Self-Generating Code" Modules
* Remove the quantum optimization module. It serves no mathematical purpose for portfolios of this scale.
* Disable any runtime code-generation features. In a real-money system, self-generating code is a critical security and operational risk. Every line of execution code must be static, version-controlled, and human-reviewed.