import { Minus, TrendingDown, TrendingUp } from 'lucide-react';
import type { Trend } from '@/lib/types';

export function TrendIcon({ trend, size = 14 }: { trend: Trend; size?: number }) {
  if (trend === 'up') return <TrendingUp size={size} color="#1F6F6B" strokeWidth={2.5} />;
  if (trend === 'down') return <TrendingDown size={size} color="#A23B2E" strokeWidth={2.5} />;
  return <Minus size={size} color="#8A8371" strokeWidth={2.5} />;
}

export function sentimentTrend(sentimiento: 'positivo' | 'negativo' | 'neutral'): Trend {
  if (sentimiento === 'positivo') return 'up';
  if (sentimiento === 'negativo') return 'down';
  return 'flat';
}
