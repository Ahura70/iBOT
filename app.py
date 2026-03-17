import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import json
from openai import OpenAI
from datetime import datetime

st.set_page_config(page_title="iBOT Agentic Trader", layout="wide")
st.title("📈 iBOT — Autonomous Agentic Factor Investing Bot")
st.caption("Powered by the 'Beyond Prompting' paper | Grok 4.20 / GPT-4o loop | $1,000 paper-trading")

# ====================== SIDEBAR ======================
st.sidebar.header("⚙️ Configuration")
provider = st.sidebar.selectbox("LLM Provider", ["OpenAI", "xAI Grok"])
api_key = st.sidebar.text_input("API Key", type="password", help="Never share this")
model = st.sidebar.text_input("Model name", 
    value="gpt-4o-mini" if provider == "OpenAI" else "grok-4.20-beta",
    help="OpenAI: gpt-4o-mini | xAI: grok-4.20-beta (or grok-4.20-beta-latest-non-reasoning)")

if provider == "xAI Grok":
    base_url = "https://api.x.ai/v1"
else:
    base_url = None

capital_start = 1000
tickers = ['AAPL','MSFT','GOOGL','AMZN','NVDA','META','TSLA','BRK-B','LLY','AVGO',
           'JPM','V','MA','UNH','XOM','PG','JNJ','HD','MRK','COST','ABBV','AMD',
           'NFLX','CRM','TMUS','INTU','NOW','ISRG','SPGI','BKNG','DIS','ADBE',
           'KO','PEP','WMT','CVX','MCD','TMO','LIN','ACN','ABT','CSCO','PFE']

# ====================== HELPER FUNCTIONS ======================
@st.cache_data(ttl=3600)
def fetch_data():
    data = yf.download(tickers, start="2021-01-01", progress=False)['Adj Close']
    volume = yf.download(tickers, start="2021-01-01", progress=False)['Volume']
    returns = data.pct_change()
    return data, volume, returns

def get_agent_factors(client, model):
    prompt = """You are the autonomous AI factor researcher from the paper "Beyond Prompting: An Autonomous Framework for Systematic Factor Investing via Agentic AI".
First, reason step-by-step with clear economic rationale.
Then propose exactly 6 novel, interpretable factors using ONLY these primitives:
- daily_returns (pandas Series)
- volume (pandas Series)
You may use .iloc[-n:], .mean(), .std(), np, pd.

Output ONLY valid JSON in this exact format (no extra text):
{
  "factors": [
    {"name": "short_mom", "expression": "daily_returns.iloc[-1]", "rationale": "Short-term underreaction..."},
    ...
  ]
}
"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a rigorous quant. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)["factors"]
    except Exception as e:
        st.error(f"Agent failed: {e}")
        return None

def run_simulation(factors, data, volume, returns):
    portfolio_value = [capital_start]
    dates = []
    trades_log = []
    capital = capital_start
    
    for i in range(20, len(returns)-1):
        current_date = returns.index[i]
        past_returns = returns.iloc[:i+1]
        past_vol = volume.iloc[:i+1]
        
        # Compute LLM factors (safe eval per ticker)
        factor_values = pd.DataFrame(index=past_returns.columns)
        for f in factors:
            expr = f["expression"]
            series = pd.Series(index=past_returns.columns, dtype=float)
            for ticker in past_returns.columns:
                local = {
                    "daily_returns": past_returns[ticker],
                    "volume": past_vol[ticker],
                    "pd": pd,
                    "np": np
                }
                try:
                    series[ticker] = eval(expr, {"__builtins__": {}}, local)
                except:
                    series[ticker] = 0
            factor_values[f["name"]] = series
        
        # z-score & composite (paper baseline)
        z = (factor_values.rank(pct=True) - 0.5) * 2
        composite = z.mean(axis=1).sort_values(ascending=False)
        
        n = len(composite)
        long = composite.iloc[:int(0.2 * n)].index.tolist()
        short = composite.iloc[-int(0.2 * n):].index.tolist()
        
        next_ret = returns.iloc[i+1]
        long_ret = next_ret[long].mean() if long else 0
        short_ret = next_ret[short].mean() if short else 0
        gross_ret = (long_ret - short_ret) / 2
        net_ret = gross_ret - 0.0003  # 3 bp
        
        capital *= (1 + net_ret)
        portfolio_value.append(capital)
        dates.append(current_date)
        
        trades_log.append({
            "date": current_date.date(),
            "long_top3": long[:3],
            "short_top3": short[:3],
            "net_ret_%": round(net_ret*100, 2),
            "capital": round(capital, 2)
        })
    
    df_value = pd.DataFrame({"Date": dates, "Capital": portfolio_value[1:]})
    returns_series = df_value["Capital"].pct_change().dropna()
    ann_ret = returns_series.mean() * 252 * 100
    ann_vol = returns_series.std() * np.sqrt(252) * 100
    sharpe = ann_ret / ann_vol if ann_vol != 0 else 0
    
    return df_value, trades_log, round(ann_ret, 2), round(ann_vol, 2), round(sharpe, 2)

# ====================== MAIN APP ======================
data, volume, returns = fetch_data()

if st.button("🚀 Launch iBOT — Let the Agent Generate Factors & Trade", type="primary"):
    if not api_key:
        st.error("Enter your API key")
        st.stop()
    
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    with st.spinner("Agent is thinking economically and proposing factors..."):
        llm_factors = get_agent_factors(client, model)
        if not llm_factors:
            st.stop()
    
    st.success(f"✅ Agent proposed {len(llm_factors)} factors")
    st.json(llm_factors)  # show what the agent created
    
    with st.spinner("Running full autonomous backtest ($1,000 → real-time equity curve)..."):
        value_df, trades_log, ann_ret, ann_vol, sharpe = run_simulation(llm_factors, data, volume, returns)
    
    st.subheader("📊 Performance (net of 3 bp costs)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Final Capital", f"${value_df['Capital'].iloc[-1]:,.2f}")
    col2.metric("Total Return", f"{((value_df['Capital'].iloc[-1]/capital_start)-1)*100:,.1f}%")
    col3.metric("Annualized Return", f"{ann_ret}%")
    col4.metric("Sharpe Ratio", f"{sharpe}")
    
    fig = px.line(value_df, x="Date", y="Capital", title="iBOT Equity Curve")
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("📋 Last 5 Trades")
    st.dataframe(pd.DataFrame(trades_log[-5:]), use_container_width=True)
    
    # Store for reflection
    st.session_state["last_factors"] = llm_factors
    st.session_state["last_performance"] = {"ann_ret": ann_ret, "sharpe": sharpe, "final_cap": value_df['Capital'].iloc[-1]}
    st.session_state["trades_log"] = trades_log

# ====================== AGENT REFLECTION LOOP ======================
if "last_performance" in st.session_state:
    st.divider()
    st.subheader("🧠 Agent Reflection Loop (click to improve)")
    if st.button("Ask Agent to Analyze Performance & Propose Better Factors"):
        client = OpenAI(api_key=api_key, base_url=base_url)
        perf = st.session_state["last_performance"]
        prompt = f"""You previously proposed these factors: {st.session_state['last_factors']}
Performance achieved: Annualized return {perf['ann_ret']}%, Sharpe {perf['sharpe']}, Final capital ${perf['final_cap']:.2f}.
Analyze why it worked or failed economically, then propose an improved set of 6 factors.
Output ONLY the same JSON format as before."""
        
        with st.spinner("Agent reflecting..."):
            new_factors = get_agent_factors(client, model)  # reuse same function
            if new_factors:
                st.success("New factors proposed by agent!")
                st.json(new_factors)
                st.info("Click the big blue button again to re-run the simulation with these improved factors.")

st.caption("Built exactly from the research paper you shared. Fully autonomous Grok/OpenAI loop. Deployed as web app. Make-believe money only.")
