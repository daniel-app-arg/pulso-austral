'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const LINKS = [
  { href: '/', label: 'Dashboard' },
  { href: '/medios', label: 'Medios' },
  { href: '/gobiernos', label: 'Por gobierno' },
  { href: '/glosario', label: 'Glosario' },
];

// El botón "Apoyá este proyecto" (Cafecito) se sacó a pedido explícito
// hasta resolver qué método de cobro usar sin exponer la identidad
// personal del operador del sitio — ver historial de conversación. La
// clase `.pa-sitenav-apoyo` en globals.css queda sin usar por ahora,
// lista para cuando se retome.

export function SiteNav() {
  const pathname = usePathname();
  return (
    <nav className="pa-sitenav">
      {LINKS.map((l) => (
        <Link key={l.href} href={l.href} className={pathname === l.href ? 'active' : ''}>
          {l.label}
        </Link>
      ))}
    </nav>
  );
}
