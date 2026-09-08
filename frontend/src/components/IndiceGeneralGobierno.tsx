import type { IndiceGeneralGobiernoDTO } from '@/lib/types';

function estadoDe(score: number): { label: string; color: string } {
  if (score >= 60) return { label: 'Mejoró', color: 'var(--teal)' };
  if (score <= 40) return { label: 'Empeoró', color: 'var(--brick)' };
  return { label: 'Estable', color: 'var(--ochre)' };
}

/** Mismo índice de difusión que el Pulso Index de arriba de todo
 * (PulsoIndexBanner), pero calculado "al inicio → al final" de ESTE
 * gobierno en vez de la última foto del país — responde si el gobierno
 * dejó más indicadores mejor o peor de como los encontró. */
export function IndiceGeneralGobierno({ data, enCurso }: { data: IndiceGeneralGobiernoDTO; enCurso: boolean }) {
  if (data.score === null) {
    return (
      <div className="pa-pulso-banner pa-pulso-banner-chico">
        <div className="pa-pulso-inner">
          <div className="pa-pulso-texto">
            <div className="pa-pulso-desglose">
              Todavía no hay suficientes indicadores comparables con datos reales para este período.
            </div>
          </div>
        </div>
      </div>
    );
  }

  const estado = estadoDe(data.score);

  return (
    <div
      className="pa-pulso-banner pa-pulso-banner-chico"
      style={{ '--estado-color': estado.color } as React.CSSProperties}
    >
      <div className="pa-pulso-inner">
        <div className="pa-pulso-score">{Math.round(data.score)}</div>
        <div className="pa-pulso-texto">
          <div className="pa-pulso-titulo">
            <span className="pa-pulso-estado">
              {enCurso ? estado.label.replace('ó', 'a') : estado.label}
            </span>
          </div>
          <div className="pa-pulso-desglose">
            Índice general del mandato — {data.mejorando} de {data.total} indicadores comparables
            mejoraron, {data.empeorando} empeoraron, {data.sin_cambio} sin cambio.
          </div>
        </div>
      </div>
    </div>
  );
}
