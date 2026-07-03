"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useCallback, useEffect, useState } from "react";
import { ApiError, clearAuthToken, requestBackend } from "@/lib/api";
import type { AuthUser } from "@/lib/types";

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
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  const loadCurrentUser = useCallback(async () => {
    setCheckingAuth(true);

    try {
      const payload = await requestBackend<{ user: AuthUser }>("/api/v1/auth/me");
      setCurrentUser(payload.user);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        clearAuthToken();
        router.replace("/login");
        return;
      }

      clearAuthToken();
      router.replace("/login");
    } finally {
      setCheckingAuth(false);
    }
  }, [router]);

  useEffect(() => {
    void loadCurrentUser();
  }, [loadCurrentUser]);

  const logout = async () => {
    try {
      await requestBackend("/api/v1/auth/logout", { method: "POST" });
    } catch {
      // Logout local continua mesmo se o token ja tiver expirado no backend.
    } finally {
      clearAuthToken();
      router.replace("/login");
    }
  };

  if (checkingAuth) {
    return <div className="loading-block auth-loading">Validando sessao...</div>;
  }

  if (!currentUser) {
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
      </aside>

      <main className="main">
        <header className="page-header">
          <div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
          </div>
          <div className="header-actions">
            <div className="user-chip" aria-label="Usuario autenticado">
              <strong>{currentUser.name}</strong>
              <span>{currentUser.role}</span>
            </div>
            {actions}
            <button className="secondary-button" type="button" onClick={logout}>
              Sair
            </button>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
