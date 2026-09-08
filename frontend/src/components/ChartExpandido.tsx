import type { PuntoSerie } from '@/lib/types';

/** Formato compacto para las etiquetas del gráfico — evita arrastrar
 * separadores de miles completos cuando el punto ya es chico (ej. "33.8"
 * en vez de "33,80" o el string es-AR completo), pero sigue mostrando
 * decimales si el dato los tiene. */
function formatearValorPunto(valor: number | string): string {
  if (typeof valor === 'string') return valor;
  const decimales = Math.min((valor.toString().split('.')[1] ?? '').length, 2);
  return valor.toLocaleString('es-AR', { minimumFractionDigits: decimales, maximumFractionDigits: decimales });
}

export function ChartExpandido({ data, color }: { data: PuntoSerie[]; color: string }) {
  const w = 600;
  const h = 190;
  const padX = 24;
  const padY = 26; // más margen arriba/abajo para que quepa la etiqueta de valor de cada punto
  const padAxis = 44; // ancho reservado a la izquierda para el eje vertical
  const valores = data.map((d) => Number(d.valor));
  const min = Math.min(...valores);
  const max = Math.max(...valores);
  const range = max - min || 1;
  const medio = (min + max) / 2;
  const anchoUtil = w - padAxis - padX;
  const stepX = data.length > 1 ? anchoUtil / (data.length - 1) : 0;
  const yDe = (v: number) => padY + (h - padY * 2) * (1 - (v - min) / range);
  const puntos = data.map((d, i) => ({
    x: padAxis + i * stepX,
    y: yDe(Number(d.valor)),
    ...d,
  }));
  const pathD = puntos.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
  const yMin = yDe(min);
  const yMax = yDe(max);
  const yMedio = yDe(medio);
  // Muchos puntos (ej. 30 días) dejan poco lugar horizontal para etiquetar
  // cada vértice sin que se pisen las etiquetas — se calcula cada cuántos
  // puntos conviene mostrar una, según el ancho estimado de cada texto
  // (la fecha es más ancha que el valor, así que salta más seguido).
  const cadaCuantoValor = Math.max(1, Math.ceil(38 / Math.max(stepX, 1)));
  const cadaCuantoFecha = Math.max(1, Math.ceil(38 / Math.max(stepX, 1)));
  const ultimo = puntos.length - 1;

  return (
    <svg viewBox={`0 0 ${w} ${h + 24}`} width="100%" style={{ display: 'block' }}>
      {/* Eje vertical: líneas de referencia en el máximo, el medio y el
          mínimo, con su valor a la izquierda. */}
      {[
        { y: yMax, v: max },
        { y: yMedio, v: medio },
        { y: yMin, v: min },
      ].map(({ y, v }, i) => (
        <g key={i}>
          <line x1={padAxis} y1={y} x2={w - padX} y2={y} stroke="#D8D2C2" strokeWidth="1" strokeDasharray={i === 1 ? '3 3' : undefined} />
          <text x={padAxis - 8} y={y} textAnchor="end" dominantBaseline="middle" fontSize="10" fill="#8A8371">
            {formatearValorPunto(v)}
          </text>
        </g>
      ))}

      <path d={pathD} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      {puntos.map((p, i) => {
        const mostrarValor = i % cadaCuantoValor === 0 || i === ultimo;
        const mostrarFecha = i % cadaCuantoFecha === 0 || i === ultimo;
        // Si el punto está cerca del techo del gráfico, el valor va abajo
        // para no salirse del viewBox.
        const arriba = p.y > padY + 10;
        return (
          <g key={i}>
            <circle cx={p.x} cy={p.y} r="3.5" fill="white" stroke={color} strokeWidth="2" />
            {mostrarValor && (
              <text
                x={p.x}
                y={arriba ? p.y - 9 : p.y + 15}
                textAnchor="middle"
                fontSize="10"
                fontWeight="600"
                fill="#3A362C"
              >
                {formatearValorPunto(p.valor)}
              </text>
            )}
            {mostrarFecha && (
              <text x={p.x} y={h + 16} textAnchor="middle" fontSize="11" fill="#5B5648">
                {p.label}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
