"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/machines", label: "Maquinas" },
  { href: "/alerts", label: "Alertas" },
  { href: "/security", label: "Seguranca" },
];

type ShellProps = {
  title: string;
  subtitle: string;
  children: ReactNode;
  actions?: ReactNode;
};

export function Shell({ title, subtitle, children, actions }: ShellProps) {
  const pathname = usePathname();

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Navegacao principal">
        <div className="brand">
          <span className="brand-mark">IT</span>
          <div>
            <strong>IT Center</strong>
            <span>Security Cloud</span>
          </div>
        </div>

        <nav className="nav-list">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link key={item.href} className={active ? "nav-link active" : "nav-link"} href={item.href}>
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      <main className="main">
        <header className="page-header">
          <div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
          </div>
          {actions ? <div className="header-actions">{actions}</div> : null}
        </header>
        {children}
      </main>
    </div>
  );
}
