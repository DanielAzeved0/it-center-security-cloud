"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useRef } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { useAuth } from "@/components/AuthProvider";

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/executive", label: "Executivo" },
  { href: "/machines", label: "Maquinas" },
  { href: "/alerts", label: "Alertas" },
  { href: "/security", label: "Seguranca" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { user, loading, logout } = useAuth();
  const mainRef = useRef<HTMLElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();

      mm.add("(prefers-reduced-motion: no-preference)", () => {
        if (!mainRef.current) {
          return;
        }

        gsap.from(mainRef.current, { autoAlpha: 0, y: 12, duration: 0.4, ease: "power2.out" });
      });

      return () => mm.revert();
    },
    { scope: mainRef, dependencies: [pathname] },
  );

  if (loading) {
    return <div className="loading-block auth-loading">Validando sessao...</div>;
  }

  if (!user) {
    return null;
  }

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

        <div className="sidebar-footer">
          <div className="sidebar-user-chip" aria-label="Usuario autenticado">
            <strong>{user.name}</strong>
            <span>{user.role}</span>
          </div>
          <button className="sidebar-logout" type="button" onClick={() => void logout()}>
            Sair
          </button>
        </div>
      </aside>

      <main className="main" ref={mainRef}>
        {children}
      </main>
    </div>
  );
}
