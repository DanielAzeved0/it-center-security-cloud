# IT Center Security Cloud — Guia para o Claude Code

Plataforma full stack de monitoramento, inventário e segurança (SOC Light) para máquinas Windows: agente PowerShell → API FastAPI → PostgreSQL → dashboard Next.js, atrás de Nginx, publicada em uma VM na Oracle Cloud.

Antes de propor mudanças de arquitetura, ferramenta ou dependência, leia `docs/` (especialmente `docs/architecture/`, `docs/backend/`, `docs/deployment/` e `docs/security/`) — a maior parte das decisões já está documentada e justificada lá, incluindo o que foi tentado e descartado (`docs/development/DECISIONS.md`, `docs/deployment/LESSONS_LEARNED.md`).

## Stack real (não sugerir substitutos sem necessidade concreta)

- **Backend:** Python + FastAPI, `psycopg` puro (sem ORM), migrations SQL manuais em `backend/migrations/`, testes com `pytest`.
- **Frontend:** Next.js (App Router) + React + TypeScript, sem Redux/Zustand/React Query — estado simples, direto.
- **Banco:** PostgreSQL.
- **Infra:** Docker Compose (dev e produção), Nginx como proxy reverso/TLS, deploy em uma única VM Ubuntu na Oracle Cloud (`itcenter-edge-01`). Sem Kubernetes, sem múltiplas clouds — é um MVP intencionalmente simples. **Terraform é exceção aprovada** (ADR-024): só para a camada abaixo do SO (VCN, subnets, security list, instância), introduzido por `terraform import` dos recursos já existentes — nunca destroy/recreate. Docker Compose, scripts de deploy/backup/restore/rollback e tudo acima do SO continuam fora do escopo do Terraform. Ver `docs/architecture/IAC.md`.
- **Agente:** PowerShell puro (`agent-windows/itcenter-agent.ps1`), sem dependências externas.
- **CI:** GitHub Actions.

Só proponha adicionar uma tecnologia nova (fila de mensagens, cache, ORM, orquestrador, etc.) se o problema concreto exigir — justifique o trade-off antes de implementar.

**Regra dura do projeto (`docs/development/CONTRIBUTING.md`):** Kubernetes, RabbitMQ, Kafka, Redis, microsserviços e Elasticsearch são explicitamente proibidos no MVP a menos que exista uma decisão formal em `docs/development/DECISIONS.md` (ADR). Qualquer mudança de arquitetura, tabela nova ou endpoint novo deve ser documentada em `docs/architecture/`, `docs/backend/DATABASE.md` ou `docs/backend/API.md` antes (ou junto) da implementação — não depois. Fluxo esperado: Planejamento → Documentação → Implementação → Teste → Deploy.

## Estado do projeto (EPICs)

O backlog fica em `docs/development/TASKS.md` (fonte de verdade, decai rápido — confira antes de assumir que algo está pendente). Snapshot: EPICs 1–13 concluídas (fundação, backend, banco, agente, dashboard, SOC Light, deploy cloud, agente em produção, validação fim a fim, dashboard operacional, SOC Light pendências, governança/autenticação, operação/segurança de produção — restore, rollback e renovação TLS já validados de verdade em produção). EPIC 16 (hardening do agente Windows — ver ADR-025), EPIC 17 (hardening do dashboard/frontend: cookie `httpOnly` de sessão, CSP, `middleware.ts`, allowlist no proxy, `npm audit` via CI) e EPIC 18 (orquestração de agentes de IA usando recursos nativos do Claude Code, sem Strix/OpenAI/Gemini — ver ADR-026 e `docs/development/AI_WORKFLOW.md`) também concluídas, a primeira exceto assinatura de código (code-signing), pendente de certificado. EPIC 14 (Wazuh, OpenVAS, multiempresa, billing, SaaS, NetBox) é futuro, fora do escopo — sem ADR/plano concreto ainda. Em 2026-08-03, 3 itens saíram de "melhorias futuras" e ganharam planejamento completo (ADR + arquitetura + backlog), mas **ainda sem código**: EPIC 19 (RustDesk + Snipe-IT, ADR-027/ADR-028), EPIC 20 (Relatórios PDF + Dashboard Executivo, ADR-029) e EPIC 21 (Prometheus + Grafana para observabilidade da infraestrutura, não das máquinas monitoradas — ADR-030). EPIC 15 (adoção de Terraform via import) concluída em 2026-08-04: recursos reais (VCN, IGW, route table, security list, subnets, instância) importados sem destroy/recreate, `terraform plan` confirmado em "No changes." Descoberta durante o import: a VCN foi criada pelo "VCN Wizard" da Oracle e já tinha NAT Gateway + Service Gateway (fora do escopo do Terraform, só referenciados por OCID) — ver `docs/architecture/IAC.md`. Backend de state remoto em OCI Object Storage segue pendente (fora do escopo mínimo da EPIC 15).

## Autenticação e autorização

Dois mecanismos separados e que não devem se misturar: agente Windows usa `X-Agent-Api-Key` (header, sem RBAC); usuários humanos usam login com Bearer token assinado por HMAC SHA-256 (`AUTH_TOKEN_SECRET`, `AUTH_TOKEN_EXPIRATION_MINUTES`), senha em PBKDF2-SHA256, papéis `admin`/`analyst`/`viewer` (ver `docs/security/AUTH.md`). O Nginx ainda aplica HTTP Basic Auth como camada extra de borda no MVP — isso não substitui o login da aplicação.

## Regras de detecção (SOC Light)

`docs/security/ASSET_POLICY.md` é a fonte de verdade sobre o que é autorizado (hostnames conhecidos, ferramentas remotas, VPNs, antivírus); `docs/security/SOC_RULES.md` define os eventos/alertas gerados a partir dessa política. Não adicione ou altere uma regra de detecção em código sem antes atualizar esses dois documentos.

## Mentalidade

- Simplicidade antes de sofisticação: este projeto propositalmente evita complexidade que não se paga ainda (ver escala real: 1 VM, poucos agentes).
- Segurança faz parte de toda mudança, não é uma etapa separada: qualquer código que toque em autenticação, dados de máquinas/usuários ou endpoints públicos deve considerar OWASP Top 10 (injection, XSS, SSRF, path traversal, controle de acesso) e o modelo de ameaças em `docs/security/SECURITY.md`.
- Ao mexer no agente Windows, no backend ou no fluxo de check-in, releia `docs/agent/CHECKIN.md` e `docs/backend/API.md` para não quebrar o contrato entre agente e API.
- Explique decisões arquiteturais não óbvias; não documente o óbvio.
- Nunca invente endpoints, variáveis de ambiente ou dependências — confira em `backend/requirements.txt`, `frontend/dashboard/package.json` e nos `.env.example` antes de assumir que algo existe.

## Testes e verificação

- Backend: `pytest` a partir de `backend/` (ver `backend/tests/`).
- Frontend: `npm run lint` e `npm run build` em `frontend/dashboard/`.
- Antes de considerar uma mudança de infra pronta, verificar os scripts em `infra/scripts/` (`preflight-production.sh`, `ops-check.sh`, `docker-scout-gate.sh`) em vez de recriar verificações do zero.

## Documentação

Ao concluir uma mudança relevante, atualize o doc correspondente em `docs/` (não crie novos arquivos soltos na raiz) e, se for uma decisão de deploy/produção, registre em `docs/deployment/DEPLOYMENT_HISTORY.md` ou `CHANGELOG_DEPLOYMENT.md` seguindo o padrão já usado nesses arquivos.
