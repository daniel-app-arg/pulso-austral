'use client';

import { useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { Historias, IndicadorVM } from '@/lib/types';
import { ChartExpandido } from './ChartExpandido';

const VENTANAS: Record<keyof Historias, number> = { dias: 30, semanas: 26, meses: 12, anios: 10 };
const NOMBRES: Record<keyof Historias, string> = { dias: 'Días', semanas: 'Semanas', meses: 'Meses', anios: 'Años' };
const ORDEN: (keyof Historias)[] = ['dias', 'semanas', 'meses', 'anios'];

export function IndicadorModal({
  indicador,
  color,
  onCerrar,
}: {
  indicador: IndicadorVM;
  color: string;
  onCerrar: () => void;
}) {
  const historias = indicador.historias as Historias;
  const granularidadesDisponibles = useMemo(
    () => ORDEN.filter((g) => (historias[g]?.length ?? 0) > 0),
    [historias],
  );
  const [granularidad, setGranularidad] = useState<keyof Historias>(
    granularidadesDisponibles.includes('meses') ? 'meses' : granularidadesDisponibles[0],
  );
  const [ventanaOffset, setVentanaOffset] = useState(0);

  function cambiarGranularidad(g: keyof Historias) {
    setGranularidad(g);
    setVentanaOffset(0);
  }

  const serie = historias[granularidad] ?? [];
  const ventana = VENTANAS[granularidad];
  const fin = serie.length - ventanaOffset;
  const inicio = Math.max(0, fin - ventana);
  const ventanaDatos = serie.slice(inicio, fin);
  const rangoLabel = ventanaDatos.length ? `${ventanaDatos[0].label} — ${ventanaDatos[ventanaDatos.length - 1].label}` : '';

  return (
    <div className="pa-modal-backdrop" onClick={onCerrar}>
      <div className="pa-modal" onClick={(e) => e.stopPropagation()}>
        <div className="pa-modal-header">
          <div>
            <div className="pa-modal-label">{indicador.label}</div>
            <div className="pa-modal-value" style={{ color }}>
              {indicador.valor}
            </div>
          </div>
          <button className="pa-modal-close" onClick={onCerrar}>
            Cerrar
          </button>
        </div>

        {granularidadesDisponibles.length > 1 && (
          <div className="pa-granularidad-row">
            {granularidadesDisponibles.map((g) => (
              <button
                key={g}
                className={`pa-granularidad-btn ${granularidad === g ? 'active' : ''}`}
                onClick={() => cambiarGranularidad(g)}
              >
                {NOMBRES[g]}
              </button>
            ))}
          </div>
        )}

        <div className="pa-timeline-nav">
          <button
            className="pa-timeline-navbtn"
            onClick={() => setVentanaOffset((o) => Math.min(o + ventana, Math.max(0, serie.length - 1)))}
            disabled={ventanaOffset + ventana >= serie.length}
            aria-label="Período anterior"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="pa-timeline-month-label">{rangoLabel}</span>
          <button
            className="pa-timeline-navbtn"
            onClick={() => setVentanaOffset((o) => Math.max(o - ventana, 0))}
            disabled={ventanaOffset <= 0}
            aria-label="Período siguiente"
          >
            <ChevronRight size={16} />
          </button>
        </div>

        <ChartExpandido data={ventanaDatos} color={color} />
      </div>
    </div>
  );
}
