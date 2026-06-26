import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "IT Center Security Cloud",
  description: "Dashboard operacional do IT Center Security Cloud",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
