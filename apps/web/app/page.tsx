const recommendations = [
  {
    symbol: "MSFT",
    company: "Microsoft",
    setup: "Trend continuation",
    score: 91,
    entry: "$428.20 - $431.10",
    stop: "$414.60",
    target: "$452.40",
    riskReward: "2.8:1",
    invalidation: "Close below EMA50",
  },
  {
    symbol: "NVDA",
    company: "NVIDIA",
    setup: "Breakout watch",
    score: 88,
    entry: "$128.40 - $131.00",
    stop: "$121.30",
    target: "$146.20",
    riskReward: "2.4:1",
    invalidation: "Failed breakout retest",
  },
  {
    symbol: "COST",
    company: "Costco",
    setup: "Pullback in uptrend",
    score: 84,
    entry: "$812.50 - $818.00",
    stop: "$789.20",
    target: "$862.10",
    riskReward: "2.1:1",
    invalidation: "Break below pullback support",
  },
];

export default function DashboardPage() {
  return (
    <main className="dashboard">
      <section className="masthead">
        <div>
          <p className="eyebrow">AlphaMomentum</p>
          <h1>Daily 5</h1>
          <p className="summary">
            Curated swing-trading setups with deterministic risk plans and clear invalidation rules.
          </p>
        </div>
        <div className="status" aria-label="Pipeline status">
          <span className="statusDot" />
          Mock data ready
        </div>
      </section>

      <section className="recommendationGrid" aria-label="Daily 5 recommendations">
        {recommendations.map((recommendation) => (
          <article className="recommendationCard" key={recommendation.symbol}>
            <div className="cardHeader">
              <div>
                <h2>{recommendation.symbol}</h2>
                <p>{recommendation.company}</p>
              </div>
              <strong>{recommendation.score}</strong>
            </div>

            <p className="setup">{recommendation.setup}</p>

            <dl className="metrics">
              <div>
                <dt>Entry</dt>
                <dd>{recommendation.entry}</dd>
              </div>
              <div>
                <dt>Stop</dt>
                <dd>{recommendation.stop}</dd>
              </div>
              <div>
                <dt>Target</dt>
                <dd>{recommendation.target}</dd>
              </div>
              <div>
                <dt>Risk/reward</dt>
                <dd>{recommendation.riskReward}</dd>
              </div>
            </dl>

            <div className="invalidation">
              <span>Invalidation</span>
              <p>{recommendation.invalidation}</p>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
