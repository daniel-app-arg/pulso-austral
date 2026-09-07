/** El isotipo de Pulso Austral: el Sol de Mayo atravesado por una línea de
 * pulso/electrocardiograma. Mismo SVG que el favicon (`app/icon.svg`) —
 * este componente existe para poder ponerlo junto al wordmark en el
 * header, no para duplicar el diseño. El disco es opaco, así que funciona
 * igual sobre fondo claro u oscuro sin variantes. */
export function LogoMark({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" aria-hidden="true">
      <circle cx="50" cy="50" r="30" fill="#C98A2C" />
      <polyline
        points="20,50 32,50 38,50 43,32 49,68 55,20 61,58 67,50 80,50"
        fill="none"
        stroke="#EDE7D9"
        strokeWidth="4.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
