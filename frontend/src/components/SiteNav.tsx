'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const LINKS = [
  { href: '/', label: 'Dashboard' },
  { href: '/medios', label: 'Medios' },
  { href: '/gobiernos', label: 'Por gobierno' },
  { href: '/glosario', label: 'Glosario' },
];

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
