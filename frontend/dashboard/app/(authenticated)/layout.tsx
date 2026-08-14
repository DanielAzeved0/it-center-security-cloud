import type { ReactNode } from "react";
import { AppShell } from "@/components/AppShell";
import { AuthProvider } from "@/components/AuthProvider";

export default function AuthenticatedLayout({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <AppShell>{children}</AppShell>
    </AuthProvider>
  );
}
