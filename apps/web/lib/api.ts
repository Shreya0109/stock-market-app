/**
 * API client for connecting to FastAPI backend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export interface Recommendation {
  id: number;
  symbol: string;
  recommendation_date: string;
  setup_type: string;
  entry_low: number;
  entry_high: number;
  stop_loss: number;
  target: number;
  mqs_score: number;
  put_call_ratio?: number;
  rationale: string;
  status: string;
  risk_reward: number;
}

export interface HealthResponse {
  status: string;
}

/**
 * Fetch today's recommendations
 */
export async function getRecommendations(): Promise<Recommendation[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/recommendations/today`, {
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to fetch recommendations:', error);
    return [];
  }
}

/**
 * Fetch health status
 */
export async function getHealth(): Promise<HealthResponse | null> {
  try {
    const response = await fetch(`${API_BASE_URL.replace('/api', '')}/health`, {
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Health check failed:', error);
    return null;
  }
}
