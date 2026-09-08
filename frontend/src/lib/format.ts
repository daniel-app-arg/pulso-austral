// Helpers de fecha compartidos — puertos directos de los que ya existían en
// pulso-austral.jsx, para no reinventar el formato ("7 de septiembre",
// "07 sep", etc.) al pasar de mocks a datos reales de la API.

export const MESES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
];

export function mesKey(fechaISO: string): string {
  const [y, m] = fechaISO.split('-');
  return `${y}-${m}`;
}

export function fechaCorta(fechaISO: string): string {
  const [, m, d] = fechaISO.split('-');
  return `${parseInt(d, 10)} ${MESES[parseInt(m, 10) - 1].slice(0, 3)}`;
}

export function fechaLarga(fechaISO: string): string {
  const [, m, d] = fechaISO.split('-').map(Number);
  return `${d} de ${MESES[m - 1]}`;
}

export function etiquetaDesdeFecha(fechaISO: string, granularidad: 'dia' | 'semana' | 'mes' | 'anio'): string {
  const [y, m, d] = fechaISO.split('-').map(Number);
  if (granularidad === 'anio') return String(y);
  if (granularidad === 'mes') return `${MESES[m - 1].slice(0, 3)}-${String(y).slice(2)}`;
  return `${String(d).padStart(2, '0')} ${MESES[m - 1].slice(0, 3)}`;
}

export function fechaCortaConAnio(fechaISO: string): string {
  const [y, m, d] = fechaISO.split('-');
  return `${parseInt(d, 10)} ${MESES[parseInt(m, 10) - 1].slice(0, 3)} ${y}`;
}

export function hoyLargo(): string {
  return new Date().toLocaleDateString('es-AR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });
}

/** Formatea un número con la convención es-AR (punto de miles, coma decimal),
 * preservando la cantidad de decimales que ya traía (hasta 3) en vez de
 * imponer un redondeo fijo — así "1852340" queda "1.852.340" y "50.492"
 * queda "50,492" sin perder precisión. */
export function formatearNumero(n: number): string {
  const decimales = Math.min((n.toString().split('.')[1] ?? '').length, 3);
  return n.toLocaleString('es-AR', { minimumFractionDigits: decimales, maximumFractionDigits: decimales });
}
