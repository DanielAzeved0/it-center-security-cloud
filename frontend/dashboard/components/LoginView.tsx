"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ApiError, requestBackend } from "@/lib/api";
import type { LoginResponse } from "@/lib/types";

export function LoginView() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const panelRef = useRef<HTMLElement>(null);

  useEffect(() => {
    document.title = "Login | IT Center Security Cloud";
  }, []);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();

      mm.add("(prefers-reduced-motion: no-preference)", () => {
        gsap.from(panelRef.current, { autoAlpha: 0, scale: 0.96, duration: 0.5, ease: "power2.out" });
      });

      return () => mm.revert();
    },
    { scope: panelRef },
  );

  const submitLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await requestBackend<LoginResponse>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      router.replace("/");
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError("Credenciais invalidas.");
      } else {
        setError(err instanceof Error ? err.message : "Erro inesperado.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-screen">
      <section className="login-panel" aria-labelledby="login-title" ref={panelRef}>
        <div className="brand login-brand">
          <span className="brand-mark">IT</span>
          <div>
            <strong>IT Center</strong>
            <span>Security Cloud</span>
          </div>
        </div>

        <div>
          <h1 id="login-title">Acesso administrativo</h1>
          <p>Entre com seu usuario para acessar o dashboard.</p>
        </div>

        <form className="login-form" onSubmit={submitLogin}>
          <label>
            E-mail
            <input
              autoComplete="email"
              disabled={loading}
              maxLength={255}
              onChange={(event) => setEmail(event.target.value)}
              required
              type="email"
              value={email}
            />
          </label>

          <label>
            Senha
            <input
              autoComplete="current-password"
              disabled={loading}
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </label>

          {error ? <div className="form-error" role="alert">{error}</div> : null}

          <button className="primary-button" disabled={loading} type="submit">
            {loading ? "Entrando" : "Entrar"}
          </button>
        </form>
      </section>
    </main>
  );
}
