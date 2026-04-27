# AlphaMomentum Recommender

## Product Vision
**Goal:**  
Provide entry-level traders with a curated list of 4–5 stocks that balance aggressive price velocity with systematic risk suppression.

---

## 1. Product Core Capabilities

### Automated Scanning
- Scans the broader market for high-velocity price action
- Validates movement using institutional volume signals

### Risk-Adjusted Ranking
- Filters out overextended stocks
- Identifies low-risk pullback entry points

### Sentiment Overlay
- Integrates derivative market data (Put/Call ratios)
- Detects potential momentum traps

### Dynamic Exit Guardrails
- Generates real-time stop-loss and take-profit levels
- Uses historical volatility for calculations

---

## 2. The Logic Funnel (Pipeline Architecture)

The system processes ~8,000 tickers through three layers to produce the **Final 5**.

### Layer 1: Liquidity & Quality Gate
- **Market Cap:** > $2 Billion (Mid to Large Cap)
- **Volume Profile:** Average Daily Volume (90-day) > 1,000,000 shares
- **Price Floor:** > $10.00 (avoid penny stock manipulation)

---

### Layer 2: Momentum Engine
- **Trend Confirmation:**
  - Price > EMA₅₀
  - EMA₅₀ > EMA₂₀₀
- **RSI:** 60 – 75
- **ADX (Trend Strength):** > 25

---

### Layer 3: Risk & Sentiment Filtering (The De-Risker)

| Indicator          | Threshold | Logic |
|------------------|----------|------|
| Put/Call Ratio   | < 0.80   | Bullish: Momentum supported by options traders |
| Put/Call Ratio   | > 1.20   | Warning: Possible momentum trap |
| Relative Volume  | > 2.0    | High conviction institutional participation |

---

## 3. The Scoring Algorithm

Stocks that pass all filters are ranked using the **Momentum-Quality Score (MQS):**

\[
MQS = \left( \frac{\Delta Price_{6M}}{\sigma_{Volatility}} \right) \times \left( \frac{1}{PC_{Ratio}} \right)
\]

### Interpretation
- **Numerator:** Rewards high returns with low volatility (smooth trends)
- **Denominator:** Penalizes bearish sentiment (high Put/Call ratio)

---

## 4. Feature Set: "The Daily 5"

The final output is a dashboard displaying 4–5 stock cards.

### Each Card Includes:

#### Ticker Analysis View

- **The Catalyst:**  
  AI-generated summary (e.g., earnings beat, FDA approval)

- **Entry Zone:**  
  Defined as the range between EMA₉ and EMA₂₁

---

### Exit Plan

- **Hard Stop:**  
  Entry - (2 × ATR₁₄)

- **Profit Target 1:**  
  Entry + (3 × ATR₁₄)

---

### Sentiment Gauge
- Visual representation of Put/Call ratio
- Compared against 30-day average

---

## 5. Technical Requirements & Data Inputs

### Required Data Streams

- **L1 Market Data:**
  - Real-time price, volume, OHLC

- **Options Flow Data:**
  - Equity Put/Call Ratio per ticker

- **Technical Analysis Libraries:**
  - Pandas-TA
  - TA-Lib

### Indicators Used
- RSI
- ADX
- ATR

---

## Summary

AlphaMomentum Recommender is a structured, data-driven pipeline that:
- Filters high-quality stocks
- Identifies momentum with discipline
- Applies sentiment-aware risk controls
- Produces actionable, low-noise trade recommendations