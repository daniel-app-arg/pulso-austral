import type { IndicadorVM } from '@/lib/types';
import { Sparkline } from './Sparkline';
import { TrendIcon } from './TrendIcon';

export function IndicadorCard({
  indicador,
  color,
  onAbrir,
}: {
  indicador: IndicadorVM;
  color: string;
  onAbrir?: (indicador: IndicadorVM) => void;
}) {
  const esClickeable = Boolean(indicador.historias);
  const serieSpark = indicador.historias?.meses ?? indicador.historias?.anios ?? [];

  return (
    <div
      className={`pa-card ${esClickeable ? 'pa-card-clickable' : ''}`}
      style={{ '--cat-color': color } as React.CSSProperties}
      onClick={esClickeable ? () => onAbrir?.(indicador) : undefined}
      role={esClickeable ? 'button' : undefined}
      tabIndex={esClickeable ? 0 : undefined}
    >
      <div className="pa-card-label">{indicador.label}</div>
      <div className="pa-card-value">{indicador.valor}</div>
      <div className="pa-card-delta">
        <TrendIcon trend={indicador.trend} polaridad={indicador.polaridad} size={12} />
        {indicador.delta}
      </div>
      {esClickeable && (
        <div className="pa-card-spark">
          <Sparkline data={serieSpark.slice(-7).map((h) => Number(h.valor))} color={color} />
        </div>
      )}
      {indicador.fuente && (
        <a
          className="pa-card-fuente"
          href={indicador.fuente.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
        >
          ref: {indicador.fuente.nombre}
        </a>
      )}
    </div>
  );
}
