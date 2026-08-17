const CONTENT_SECURITY_POLICY = [
  "default-src 'self'",
  // 'unsafe-inline' permanece necessario: o proprio App Router do Next.js
  // (confirmado em dev e no build standalone) injeta scripts inline sem
  // "src" e sem nonce (`self.__next_f.push(...)`, payload de streaming de
  // React Server Components usado na hidratacao) em toda pagina. Sem
  // 'unsafe-inline' e sem uma CSP baseada em nonce (que exigiria mover essa
  // policy para middleware.ts, gerando um nonce por request), o browser
  // bloqueia esses scripts e a aplicacao nao hidrata. Ver EPIC 28 em
  // docs/development/TASKS.md.
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data:",
  "font-src 'self'",
  "connect-src 'self'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join("; ");

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "Content-Security-Policy",
            value: CONTENT_SECURITY_POLICY,
          },
        ],
      },
    ];
  },
};

export default nextConfig;
