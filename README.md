# iBOT
True agentic AI that acts like a self-directed quant researcher
iBOT is the implentation of a research paper titled "Beyond Prompting: An Autonomous Framework for Systematic Factor Investing via Agentic AI," by Allen Yikuan Huang and Zheqi Fan from the Hong Kong University of Science and Technology 
The paper explores the idea of replacing manual prompting with a true agentic AI that acts like a self-directed quant researcher. It uses a closed-loop ReAct + Chain-of-Thought system to:
Generate interpretable factors from primitives (returns, volume, volatility, etc.) with economic rationale required first.
Backtest rigorously (t-IC, long-short Sharpe, no look-ahead).
Gate only the best factors (statistical + economic thresholds).
Aggregate them linearly or with LightGBM.
Form daily long-short portfolios.

Out-of-sample (2021–2024) on CRSP U.S. equities: the composite long-short delivered 59.53 % annualized return and Sharpe ratio 3.11 (net of costs in robustness checks). The framework explicitly fights data-snooping and p-hacking.
iBOT is a fully autonomous Python trading bot that implements the spirit of the paper right now, using make-believe money (paper-trading simulation).

It runs completely on its own (daily rebalancing loop).
Uses the paper’s linear-aggregation baseline (z-scored factors → composite signal → long-short decile-style portfolio).
Works on a fake starting capital of US$100,000.
3 bp transaction costs (exactly as in the paper’s robustness section).
Daily decisions, equity curve, Sharpe, and trade log — all printed live.
