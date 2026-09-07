import type { PuntoSerie } from '@/lib/types';

export function ChartExpandido({ data, color }: { data: PuntoSerie[]; color: string }) {
  const w = 600;
  const h = 190;
  const padX = 20;
  const padY = 14;
  const valores = data.map((d) => Number(d.valor));
  const min = Math.min(...valores);
  const max = Math.max(...valores);
  const range = max - min || 1;
  const stepX = data.length > 1 ? (w - padX * 2) / (data.length - 1) : 0;
  const puntos = data.map((d, i) => ({
    x: padX + i * stepX,
    y: padY + (h - padY * 2) * (1 - (Number(d.valor) - min) / range),
    ...d,
  }));
  const pathD = puntos.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');

  return (
    <svg viewBox={`0 0 ${w} ${h + 24}`} width="100%" style={{ display: 'block' }}>
      <path d={pathD} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      {puntos.map((p, i) => (
        <g key={i}>
          <circle cx={p.x} cy={p.y} r="3.5" fill="white" stroke={color} strokeWidth="2" />
          <text x={p.x} y={h + 16} textAnchor="middle" fontSize="11" fill="#5B5648">
            {p.label}
          </text>
        </g>
      ))}
    </svg>
  );
}
