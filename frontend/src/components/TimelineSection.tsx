'use client';

import { useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight, Clock } from 'lucide-react';
import type { EventoTimelineVM, Sentimiento } from '@/lib/types';
import { MESES, fechaCortaConAnio, mesKey } from '@/lib/format';
import { TrendIcon, sentimentTrend } from './TrendIcon';

function TimelineItem({ ev }: { ev: EventoTimelineVM }) {
  return (
    <div className="pa-timeline-item">
      <div className={`pa-timeline-dot pa-dot-${ev.sentimiento}`}>
        <TrendIcon trend={sentimentTrend(ev.sentimiento)} size={11} />
      </div>
      <div className="pa-timeline-content">
        <span className="pa-timeline-fecha">{fechaCortaConAnio(ev.fecha)}</span>
        <span className="pa-timeline-titulo">{ev.titulo}</span>
      </div>
    </div>
  );
}

export function TimelineSection({ timeline }: { timeline: EventoTimelineVM[] }) {
  const [expandido, setExpandido] = useState(false);
  const [mesIdx, setMesIdx] = useState(0);

  const ordenado = useMemo(() => [...timeline].sort((a, b) => (a.fecha < b.fecha ? 1 : -1)), [timeline]);
  const reciente = ordenado.slice(0, 6);

  const mesesDisponibles = useMemo(() => {
    return Array.from(new Set(ordenado.map((ev) => mesKey(ev.fecha))))
      .sort()
      .reverse()
      .map((key) => {
        const [y, m] = key.split('-');
        return { key, label: `${MESES[parseInt(m, 10) - 1]} ${y}` };
      });
  }, [ordenado]);

  const mesActual = mesesDisponibles[mesIdx];
  const eventosDelMes = ordenado.filter((ev) => mesKey(ev.fecha) === mesActual?.key);
  const resumenMes = eventosDelMes.reduce<Record<Sentimiento, number>>(
    (acc, ev) => {
      acc[ev.sentimiento] = (acc[ev.sentimiento] || 0) + 1;
      return acc;
    },
    { positivo: 0, negativo: 0, neutral: 0 },
  );

  return (
    <>
      <div className="pa-section-title">
        <Clock size={18} />
        Línea de tiempo
      </div>

      {!expandido ? (
        <div className="pa-timeline">
          {reciente.map((ev, i) => (
            <TimelineItem ev={ev} key={i} />
          ))}
          <button className="pa-timeline-toggle" onClick={() => setExpandido(true)}>
            Ver línea de tiempo completa
          </button>
        </div>
      ) : (
        <div className="pa-timeline-expanded">
          <div className="pa-timeline-nav">
            <button
              className="pa-timeline-navbtn"
              onClick={() => setMesIdx((i) => Math.min(i + 1, mesesDisponibles.length - 1))}
              disabled={mesIdx >= mesesDisponibles.length - 1}
              aria-label="Mes anterior"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="pa-timeline-month-label">{mesActual?.label}</span>
            <button
              className="pa-timeline-navbtn"
              onClick={() => setMesIdx((i) => Math.max(i - 1, 0))}
              disabled={mesIdx <= 0}
              aria-label="Mes siguiente"
            >
              <ChevronRight size={16} />
            </button>
            <button className="pa-timeline-toggle pa-timeline-close" onClick={() => setExpandido(false)}>
              Cerrar línea de tiempo
            </button>
          </div>

          <div className="pa-timeline-summary">
            <div className="pa-summary-stat">
              <span className="pa-summary-num" style={{ color: '#1F6F6B' }}>{resumenMes.positivo}</span>
              <span className="pa-summary-lbl">Noticias positivas</span>
            </div>
            <div className="pa-summary-stat">
              <span className="pa-summary-num" style={{ color: '#A23B2E' }}>{resumenMes.negativo}</span>
              <span className="pa-summary-lbl">Noticias negativas</span>
            </div>
            <div className="pa-summary-stat">
              <span className="pa-summary-num" style={{ color: '#8A8371' }}>{resumenMes.neutral}</span>
              <span className="pa-summary-lbl">Noticias neutras</span>
            </div>
          </div>
          <div className="pa-summary-fuente">
            Clasificación propia en base a cobertura de medios nacionales —{' '}
            <a href="https://news.google.com/search?q=argentina%20econom%C3%ADa&hl=es-419&gl=AR&ceid=AR%3Aes-419" target="_blank" rel="noopener noreferrer">
              ver fuentes
            </a>
          </div>

          <div className="pa-timeline">
            {eventosDelMes.length === 0 && (
              <div className="pa-timeline-vacio">No hay eventos registrados este mes.</div>
            )}
            {eventosDelMes.map((ev, i) => (
              <TimelineItem ev={ev} key={i} />
            ))}
          </div>
        </div>
      )}
    </>
  );
}
