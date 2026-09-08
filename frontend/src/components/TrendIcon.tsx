import { Minus, TrendingDown, TrendingUp } from 'lucide-react';
import type { Trend } from '@/lib/types';

type Polaridad = 'positivo' | 'negativo' | 'neutral';

const VERDE = '#1F6F6B';
const ROJO = '#A23B2E';
const GRIS = '#8A8371';

/** El color de la flecha depende de si esa dirección es buena o mala para
 * el indicador, no solo de si el valor subió o bajó — un indicador con
 * polaridad "negativo" (ej. riesgo país, desempleo) mejora cuando BAJA, así
 * que ahí "down" tiene que pintarse verde, no rojo. Sin polaridad (u
 * "positivo"/omitida) se mantiene la lectura literal: sube=verde, baja=rojo. */
function colorSegunPolaridad(trend: Trend, polaridad?: Polaridad): string {
  if (trend === 'flat' || !polaridad || polaridad === 'neutral') {
    return trend === 'up' ? VERDE : trend === 'down' ? ROJO : GRIS;
  }
  const esMejora = (polaridad === 'positivo' && trend === 'up') || (polaridad === 'negativo' && trend === 'down');
  return esMejora ? VERDE : ROJO;
}

export function TrendIcon({ trend, polaridad, size = 14 }: { trend: Trend; polaridad?: Polaridad; size?: number }) {
  const color = colorSegunPolaridad(trend, polaridad);
  if (trend === 'up') return <TrendingUp size={size} color={color} strokeWidth={2.5} />;
  if (trend === 'down') return <TrendingDown size={size} color={color} strokeWidth={2.5} />;
  return <Minus size={size} color={GRIS} strokeWidth={2.5} />;
}

export function sentimentTrend(sentimiento: 'positivo' | 'negativo' | 'neutral'): Trend {
  if (sentimiento === 'positivo') return 'up';
  if (sentimiento === 'negativo') return 'down';
  return 'flat';
}
