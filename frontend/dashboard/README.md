# Dashboard

Dashboard web do IT Center Security Cloud construido com Next.js e TypeScript.

## Execucao recomendada

Use o Docker Compose da raiz do projeto:

```powershell
docker compose -f infra/docker-compose.yml up --build
```

URL local:

```text
http://127.0.0.1:3000
```

No Docker Compose, o dashboard aponta para o backend pelo DNS interno:

```text
ITCENTER_API_BASE_URL=http://backend:8000
```

## Requisitos para execucao manual

```text
Node.js 22+
npm
Backend FastAPI em execucao
```

## Configuracao

O dashboard usa um proxy interno em:

```text
/api/backend/...
```

Por padrao, o proxy aponta para:

```text
http://127.0.0.1:8000
```

Para alterar:

```powershell
$env:ITCENTER_API_BASE_URL="http://127.0.0.1:8000"
```

## Execucao manual

```powershell
cd frontend/dashboard
npm install
npm run dev
```

URL local:

```text
http://127.0.0.1:3000
```

## Telas

```text
/login     Login administrativo (Bearer token, RBAC)
/          Dashboard operacional
/executive Dashboard executivo (resumo agregado + exportar PDF)
/machines  Inventario, metricas e programas
/alerts    Alertas e acao de resolver
/security  Eventos de seguranca
```

Em `/executive` e no detalhe de maquina (`/machines/[id]`), o botao "Exportar PDF" baixa um relatorio gerado pelo backend (`reportlab`) via `GET /api/v1/reports/executive.pdf` e `GET /api/v1/machines/{id}/report.pdf`.

## Proxy /api/backend: allowlist e defesa contra path traversal

`app/api/backend/[...path]/route.ts` so repassa para o backend paths que comecem por um destes prefixos (`ALLOWED_PATH_PREFIXES`):

```text
api/v1/health
api/v1/auth/login, api/v1/auth/me, api/v1/auth/logout
api/v1/machines
api/v1/alerts
api/v1/security-events
api/v1/dashboard
api/v1/reports
```

Qualquer path fora dessa lista recebe `404` antes de qualquer chamada ao backend real. Os endpoints do agente (`api/v1/agent/*`) nao estao nessa lista de proposito — o agente Windows fala direto com o backend, nunca atraves deste proxy do dashboard.

Antes de checar a allowlist, `toSafeSegments()` rejeita com `404` qualquer segmento vazio, `.` ou `..` (incluindo `/`/`\` codificados dentro de um unico segmento, ex.: `machines%2f..%2f..%2f..%2fdocs`) — correcao de um bypass de path traversal real encontrado na auditoria de 2026-08-15 (EPIC 28-B): a checagem de allowlist rodava sobre o path ainda codificado, mas a URL final era montada depois com `new URL(...)`, que normaliza `..` nesse momento, permitindo escapar da allowlist. Ver `docs/security/SECURITY.md` para o achado completo.

## middleware.ts: gate de sessao no edge

`middleware.ts` roda no edge antes de renderizar `/`, `/machines`, `/machines/:path*`, `/alerts`, `/security` e `/executive` (`config.matcher`): se o cookie de sessao `itcenter_session` nao estiver presente, redireciona para `/login` sem sequer chegar a montar a pagina. E so uma checagem de presenca do cookie (rapida, no edge, sem round-trip ao backend) — a validacao de verdade do token (assinatura HMAC, expiracao, RBAC por rota) continua sendo feita pelo backend a cada chamada de API; o middleware existe para nao piscar conteudo protegido antes do redirect, nao para substituir a autorizacao real.

## Layout e autenticacao (EPIC 26)

As 6 telas autenticadas vivem em `app/(authenticated)/` (route group — nao afeta a URL), com `app/(authenticated)/layout.tsx` montando `AuthProvider` (`components/AuthProvider.tsx`, busca `GET /api/v1/auth/me` uma unica vez por sessao e expõe `useAuth()`) e `AppShell` (`components/AppShell.tsx`, sidebar/nav persistente + chip do usuario/"Sair"). Isso existe para navegacao entre telas nao remontar a sidebar nem repetir o fetch de autenticacao a cada clique (antes, cada `*View.tsx` chamava seu proprio `<Shell>`, que desmontava e refazia o auth-check em toda troca de rota). Cada `*View.tsx` renderiza seu proprio `<header className="page-header">` (titulo/subtitulo/acoes) e le `currentUser`/`role` via `useAuth()` em vez de buscar `/auth/me` de novo.

## Animacoes (GSAP)

`gsap` e `@gsap/react` (hook `useGSAP`) sao usados para polimento visual (entrada de cards/listas, contadores animados, preenchimento das barras de metrica) em todas as telas. Toda animacao respeita `prefers-reduced-motion` via `gsap.matchMedia()` — ver `lib/motion.ts` (hook `useStaggerEntrance` e helpers `animateCountUp`/`animateProgressValue`, reaproveitados pelos componentes de tela). Instrucoes de uso corretas da API ficam na skill `.agents/skills/gsap-*` (ver `docs/development/AI_WORKFLOW.md`).

## Design system (tokens e componentes compartilhados)

Sem Tailwind/CSS Modules/CSS-in-JS: um unico `app/globals.css` com tokens via CSS custom properties no `:root` (cor, tipografia, espacamento, radius, sombra), incluindo **dark mode automatico** via `@media (prefers-color-scheme: dark)` (sem toggle manual). A paleta semantica (`--success`/`--warning`/`--danger`/`--info`/`--critical`) e a mesma usada por `StatusBadge`/`SeverityBadge` (`.badge`) e pelas variantes de cor do `StatCard` (prop `tone`), para o mesmo significado ter sempre a mesma cor em qualquer tela. `components/Ui.tsx` tambem exporta `Panel` (title/meta/actions/children), usado no lugar de repetir `<section className="panel"><div className="panel-header">` em cada view.

Referencia de inspiracao (EPIC 25, `docs/development/TASKS.md`): "design DNA" extraido do Snipe-IT (admin panel do mesmo dominio) via a skill `zanwei/design-dna` — usado como referencia de padrao de organizacao (KPIs coloridos, sidebar escura + conteudo claro), nao como paleta literal.

## Seguranca de dependencias

O dashboard usa Next.js `16.2.12`, `picomatch` `4.0.4` e `overrides` de `postcss`/`sharp`/`nanoid` (`8.5.25`/`0.35.3`/`3.3.18`) em `package.json` para fechar CVEs high de dependencias internas do Next que a versao atual ainda nao corrigiu. O override de `nanoid` (`3.3.18`) foi adicionado para corrigir a `GHSA-2v37-7h3g-55p8` em uma dependencia transitiva de `postcss`.

Durante o build Docker, o script abaixo substitui o `picomatch` compilado dentro do Next.js pela versao corrigida instalada no projeto:

```text
scripts/security/patch-next-picomatch.js
```

Esse script roda antes de `npm run build` no `Dockerfile`.

A imagem final roda o Next.js diretamente com `node` e remove o `npm` global da camada de runtime. Isso evita carregar dependencias internas do npm que nao sao necessarias para executar o dashboard e podem aparecer no Docker Scout.

Validacao recomendada apos build da imagem:

```powershell
docker scout cves infra-frontend:latest --only-severity critical,high
```
