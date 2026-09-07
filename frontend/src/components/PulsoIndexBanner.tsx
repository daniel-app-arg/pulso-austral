'use client';

import { useState } from 'react';
import type { PulsoIndexDTO } from '@/lib/types';
import { TrendIcon } from './TrendIcon';

function estadoDe(score: number): { label: string; color: string } {
  if (score >= 60) return { label: 'Mejorando', color: 'var(--teal)' };
  if (score <= 40) return { label: 'Empeorando', color: 'var(--brick)' };
  return { label: 'Estable', color: 'var(--ochre)' };
}

const ICONO_DIRECCION = { mejora: 'up', empeora: 'down', sin_cambio: 'flat' } as const;

export function PulsoIndexBanner({ data }: { data: PulsoIndexDTO }) {
  const [abierto, setAbierto] = useState(false);
  const estado = estadoDe(data.score);

  return (
    <div className="pa-pulso-banner" style={{ '--estado-color': estado.color } as React.CSSProperties}>
      <div className="pa-pulso-inner">
        <div className="pa-pulso-score">{Math.round(data.score)}</div>
        <div className="pa-pulso-texto">
          <div className="pa-pulso-titulo">
            <span className="pa-pulso-estado">{estado.label}</span>
            {data.trend && data.delta !== null && (
              <span className="pa-pulso-delta">
                <TrendIcon trend={data.trend} size={12} />
                {data.delta >= 0 ? '+' : ''}
                {data.delta.toFixed(1)} desde la foto anterior
              </span>
            )}
          </div>
          <div className="pa-pulso-desglose">
            Índice general — {data.mejorando} de {data.total} indicadores comparables mejoran,{' '}
            {data.empeorando} empeoran, {data.sin_cambio} sin cambio.
          </div>
        </div>
        <button className="pa-pulso-toggle" onClick={() => setAbierto((a) => !a)}>
          {abierto ? 'Ocultar metodología' : '¿Cómo se calcula?'}
        </button>
      </div>

      {abierto && (
        <div className="pa-pulso-detalle">
          <p className="pa-pulso-metodologia">
            Se cuenta, entre los indicadores donde hay consenso amplio sobre qué dirección es una
            mejora, cuántos vienen mejorando y cuántos empeorando desde su último dato — el mismo
            trend que ya se ve en cada tarjeta. El score es 50 + 50 × (mejoran − empeoran) / total:
            50 es tantos mejorando como empeorando, 100 es todos mejorando, 0 es todos empeorando.
            Quedan afuera a propósito los indicadores sin una dirección de consenso — dólar, Merval,
            todo lo de desarrollo militar, aprobación y confianza en el gobierno, gasto público, y
            canasta básica (nominal, siempre sube con inflación) — meterlos obligaría a asumir una
            postura ideológica disfrazada de medición objetiva.
          </p>
          <div className="pa-pulso-lista">
            {data.detalle.map((d) => (
              <span className="pa-pulso-item" key={d.id}>
                <TrendIcon trend={ICONO_DIRECCION[d.direccion]} size={12} />
                <b>{d.nombre}</b>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
