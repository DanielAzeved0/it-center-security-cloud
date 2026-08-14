"use client";

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { requestBackend } from "@/lib/api";
import type { AuthUser } from "@/lib/types";

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const loadCurrentUser = useCallback(async () => {
    setLoading(true);

    try {
      const payload = await requestBackend<{ user: AuthUser }>("/api/v1/auth/me");
      setUser(payload.user);
    } catch {
      router.replace("/login");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    void loadCurrentUser();
  }, [loadCurrentUser]);

  const logout = useCallback(async () => {
    try {
      await requestBackend("/api/v1/auth/logout", { method: "POST" });
    } catch {
      // O cookie de sessao e limpo pelo proxy mesmo se a chamada ao backend falhar.
    } finally {
      router.replace("/login");
    }
  }, [router]);

  return <AuthContext.Provider value={{ user, loading, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth deve ser usado dentro de <AuthProvider>");
  }

  return context;
}
