/**
 * RecommendationCard component for displaying a single stock recommendation.
 */

import { Recommendation } from '@/lib/api';

export interface RecommendationCardProps {
  recommendation: Recommendation;
}

export function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const formatPrice = (price: number) => `$${price.toFixed(2)}`;

  return (
    <div className="recommendationCard">
      <div className="cardHeader">
        <div>
          <h2>{recommendation.symbol}</h2>
          <p>{recommendation.setup_type}</p>
        </div>
        <strong>{recommendation.mqs_score.toFixed(1)}</strong>
      </div>

      <div className="setup">
        {recommendation.setup_type.charAt(0).toUpperCase() + recommendation.setup_type.slice(1)}
      </div>

      <div className="metrics">
        <div>
          <dt>Entry Zone</dt>
          <dd>
            {formatPrice(recommendation.entry_low)} → {formatPrice(recommendation.entry_high)}
          </dd>
        </div>
        <div>
          <dt>Stop Loss</dt>
          <dd>{formatPrice(recommendation.stop_loss)}</dd>
        </div>
        <div>
          <dt>Target</dt>
          <dd>{formatPrice(recommendation.target)}</dd>
        </div>
        <div>
          <dt>Risk/Reward</dt>
          <dd>{recommendation.risk_reward.toFixed(2)}:1</dd>
        </div>
      </div>

      <p style={{ fontSize: '0.95rem', lineHeight: '1.4', marginBottom: '0' }}>
        {recommendation.rationale}
      </p>

      {recommendation.put_call_ratio && (
        <div style={{ marginTop: '12px', fontSize: '0.85rem', color: 'var(--muted)' }}>
          Put/Call Ratio: {recommendation.put_call_ratio.toFixed(2)}
        </div>
      )}
    </div>
  );
}
