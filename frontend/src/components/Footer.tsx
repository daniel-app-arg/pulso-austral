import Link from 'next/link';

export function Footer() {
  return (
    <div className="pa-footer">
      Cada indicador cita su fuente real (INDEC, BCRA y otros organismos y encuestadoras) — el que todavía no tiene un dato verificado se muestra vacío en vez de inventado. Ver{' '}
      <Link href="/glosario">glosario</Link> para el detalle.
    </div>
  );
}
