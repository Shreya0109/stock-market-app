'use client';

import { useState, useEffect } from 'react';
import { getRecommendations, Recommendation } from '@/lib/api';
import { RecommendationCard } from '@/components/RecommendationCard';

const MOCK_RECOMMENDATIONS: Recommendation[] = [
  {
    id: 1,
    symbol: 'MSFT',
    recommendation_date: new Date().toISOString(),
    setup_type: 'continuation',
    entry_low: 428.2,
    entry_high: 431.1,
    stop_loss: 414.6,
    target: 452.4,
    mqs_score: 91,
    rationale: 'Trend continuation with strong volume confirmation above EMA50',
    status: 'open',
    risk_reward: 2.8,
  },
  {
    id: 2,
    symbol: 'NVDA',
    recommendation_date: new Date().toISOString(),
    setup_type: 'breakout',
    entry_low: 128.4,
    entry_high: 131.0,
    stop_loss: 121.3,
    target: 146.2,
    mqs_score: 88,
    rationale: 'Breakout watch with RSI in optimal range and ADX > 25',
    status: 'open',
    risk_reward: 2.4,
  },
  {
    id: 3,
    symbol: 'COST',
    recommendation_date: new Date().toISOString(),
    setup_type: 'pullback',
    entry_low: 812.5,
    entry_high: 818.0,
    stop_loss: 789.2,
    target: 862.1,
    mqs_score: 84,
    rationale: 'Pullback in uptrend with support holding',
    status: 'open',
    risk_reward: 2.1,
  },
];

export default function DashboardPage() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>(MOCK_RECOMMENDATIONS);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchRecommendations() {
      try {
        setIsLoading(true);
        const data = await getRecommendations();
        if (data.length > 0) {
          setRecommendations(data);
        } else {
          setError('No recommendations available. Using mock data.');
        }
      } catch (err) {
        console.error('Error fetching recommendations:', err);
        setError('Failed to fetch recommendations. Using mock data.');
      } finally {
        setIsLoading(false);
      }
    }

    fetchRecommendations();
  }, []);

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
          {isLoading ? 'Loading...' : 'Data ready'}
        </div>
      </section>

      {error && (
        <div
          style={{
            marginBottom: '24px',
            padding: '12px',
            borderRadius: '6px',
            backgroundColor: 'var(--danger-soft)',
            color: 'var(--danger)',
            fontSize: '0.9rem',
          }}
        >
          {error}
        </div>
      )}

      <section className="recommendationGrid" aria-label="Daily 5 recommendations">
        {recommendations.map((rec) => (
          <RecommendationCard key={rec.symbol} recommendation={rec} />
        ))}
      </section>

      <div
        style={{
          marginTop: '32px',
          padding: '16px',
          borderRadius: '8px',
          backgroundColor: '#f0f9f8',
          fontSize: '0.85rem',
          color: 'var(--muted)',
        }}
      >
        <strong style={{ color: 'var(--text)' }}>Educational Disclaimer:</strong> This platform
        provides educational trade ideas only. It does not provide personalized financial advice.
        Always do your own research and consult with a financial advisor.
      </div>
    </main>
  );
}
