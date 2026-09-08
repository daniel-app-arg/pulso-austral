'use client';

import { useEffect, useState } from 'react';
import type { DashboardData } from '@/lib/types';
import { hoyLargo } from '@/lib/format';
import { LogoMark } from './LogoMark';
import { SiteNav } from './SiteNav';
import { TrendIcon } from './TrendIcon';

export function Masthead({ destacados, ticker, fuenteDatos }: Pick<DashboardData, 'destacados' | 'ticker' | 'fuenteDatos'>) {
  const [loaded, setLoaded] = useState(false);
  // Lazy init: se calcula una sola vez al montar, en cliente — evita fijar la
  // fecha "de hoy" en el momento del build/SSR.
  const [hoy] = useState(() => hoyLargo());

  useEffect(() => {
    const t = setTimeout(() => setLoaded(true), 60);
    return () => clearTimeout(t);
  }, []);

  const estado = fuenteDatos === 'api' ? 'conectado' : 'demo';

  return (
    <div className="pa-masthead">
      <div className="pa-masthead-top">
        <div className="pa-brand">
          <LogoMark size={34} />
          <div>
            <h1 className="pa-title pa-serif">Pulso Austral</h1>
            <div className="pa-tagline">El estado del país, medido.</div>
          </div>
        </div>
        <div className="pa-date">
          {hoy}
          <span className={`pa-estado-conexion pa-estado-${estado}`}>
            {estado === 'conectado' ? '● datos en vivo' : '○ datos de ejemplo'}
          </span>
        </div>
      </div>

      <SiteNav />

      <div className={`pa-dollars ${loaded ? 'pa-loaded' : ''}`}>
        <div className="pa-dollar-block">
          <div className="pa-dollar-label">Dólar oficial</div>
          <div className="pa-dollar-value">${destacados.dolares.oficial.valor.toLocaleString('es-AR')}</div>
          <div className="pa-dollar-delta">
            <TrendIcon trend={destacados.dolares.oficial.delta > 0 ? 'up' : 'down'} />
            {Math.abs(destacados.dolares.oficial.delta)}% hoy
          </div>
        </div>
        <div className="pa-dollar-block">
          <div className="pa-dollar-label">Dólar blue</div>
          <div className="pa-dollar-value">${destacados.dolares.blue.valor.toLocaleString('es-AR')}</div>
          <div className="pa-dollar-delta">
            <TrendIcon trend={destacados.dolares.blue.delta > 0 ? 'up' : 'down'} />
            {Math.abs(destacados.dolares.blue.delta)}% hoy
          </div>
        </div>
        <div className="pa-dollar-block">
          <div className="pa-dollar-label">Merval</div>
          {destacados.merval ? (
            <>
              <div className="pa-dollar-value">{destacados.merval.valor.toLocaleString('es-AR')}</div>
              <div className="pa-dollar-delta">
                <TrendIcon trend={destacados.merval.delta > 0 ? 'up' : 'down'} />
                {Math.abs(destacados.merval.delta)}% hoy
              </div>
            </>
          ) : (
            <>
              <div className="pa-dollar-value">—</div>
              <div className="pa-dollar-delta">sin fuente real disponible</div>
            </>
          )}
        </div>
        <div className="pa-brecha">
          <div className="pa-brecha-value">{destacados.brecha}%</div>
          <div className="pa-brecha-label">brecha cambiaria</div>
        </div>
      </div>

      <div className="pa-ticker-wrap">
        <div className="pa-ticker">
          {[...ticker, ...ticker].map((item, i) => (
            <span className="pa-ticker-item" key={i}>
              {item.label} <b>{item.valor}</b> <TrendIcon trend={item.trend} polaridad={item.polaridad} size={12} />
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
