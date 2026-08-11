# AI_WORKFLOW.md

# Orquestração de Agentes de IA no IT Center Security Cloud

## Objetivo

Documentar como o Claude Code é configurado para atuar como especialistas de domínio (backend, frontend, devops, security, architecture, documentation) neste repositório, e por que a solução adotada usa apenas recursos nativos do Claude Code em vez de um framework de orquestração próprio. Decisão registrada em ADR-026 (`docs/development/DECISIONS.md`).

---

# O que existe

## Subagents (`.claude/agents/`)

Seis subagents de projeto, cada um com um `description` que o Claude Code usa para roteamento automático (a tarefa é direcionada ao agente certo mesmo sem chamar o comando explicitamente) e um prompt curto apontando para os documentos de fonte-da-verdade do domínio:

| Agente | Domínio | Doc de referência principal |
| --- | --- | --- |
| `backend` | FastAPI, psycopg, migrations | `docs/backend/API.md`, `docs/backend/DATABASE.md` |
| `frontend` | Next.js, React, TypeScript | `docs/security/AUTH.md` (RBAC de UI), `frontend/dashboard/package.json` |
| `devops` | Docker Compose, Nginx, Terraform, CI/CD (inclui SRE) | `docs/architecture/ARCHITECTURE.md`, `docs/deployment/PRODUCTION.md`, `infra/scripts/` |
| `security` | OWASP, SOC Light, autenticação | `docs/security/SECURITY.md`, `docs/security/AUTH.md`, `docs/security/ASSET_POLICY.md`, `docs/security/SOC_RULES.md` |
| `architecture` | Impacto estrutural, ADRs | `docs/architecture/ARCHITECTURE.md`, `docs/development/DECISIONS.md` |
| `documentation` | Sincronizar `docs/` | `docs/development/CONTRIBUTING.md` (seção "Fonte da Verdade") |

Não existe um agente `sre` separado: na escala atual (uma VM, sem equipe de SRE dedicada) essas responsabilidades ficam dentro do agente `devops`.

## Skills externas (`.agents/skills/`)

Além dos subagents de projeto, o repositório também versiona skills de terceiros instaladas via `npx skills add` (ferramenta `skills.sh`) quando uma biblioteca específica exige instruções corretas de uso que vão além do conhecimento geral do modelo:

* **gsap-skills** (`greensock/gsap-skills`, oficial GreenSock) — 5 das 8 skills do pacote (`gsap-core`, `gsap-react`, `gsap-timeline`, `gsap-performance`, `gsap-utils`), instaladas em 2026-08-11 para o polimento de animações do dashboard (EPIC 24). As 3 restantes (`gsap-frameworks`, `gsap-scrolltrigger`, `gsap-plugins`) não foram instaladas por não se aplicarem ao projeto: `gsap-frameworks` é para Vue/Svelte (o dashboard é React/Next.js), e `gsap-scrolltrigger`/`gsap-plugins` (Flip, Draggable, SVG drawing, scroll-linked animation) não têm caso de uso identificado numa aplicação interna de operação, sem páginas de rolagem longa.

O conteúdo real das skills fica em `.agents/skills/<nome>/SKILL.md` (versionado). `.claude/skills/<nome>` são symlinks absolutos gerados por máquina — **não versionados** (`.gitignore`), regeneráveis com `npx skills experimental_install` (lê `skills-lock.json`, também versionado) em qualquer novo checkout.

## Slash commands (`.claude/commands/`)

`/backend`, `/frontend`, `/devops`, `/security`, `/architecture` e `/docs` apenas delegam a tarefa ao subagent correspondente — são um jeito explícito de escolher o agente quando o roteamento automático não é suficiente.

`/feature` roda um pipeline completo usando a ferramenta Workflow nativa do Claude Code: `architecture → implementation → (review + security em paralelo) → docs`. O estágio de review cobre qualidade/simplificação do código; o de security cobre OWASP Top 10 e as regras de `docs/security/`.

---

# O que foi deliberadamente descartado (e por quê)

O plano original que inspirou esta convenção propunha um framework Python próprio (`.agent/`) com abstração de múltiplos providers (Strix, Claude, OpenAI, Gemini), roteador customizado, biblioteca de prompts em YAML, cache de tarefas, CLI própria e logging customizado.

Isso foi reduzido porque:

* **Subagents + roteamento por `description` já resolvem** o que o plano chamava de "AgentManager" e "Router Inteligente" — não há necessidade de reimplementar isso em Python.
* **A ferramenta Workflow já resolve** o que o plano chamava de "Pipeline Engine" (Fase 8) — `/feature` usa exatamente essa ferramenta.
* **Strix, OpenAI e Gemini não foram adotados.** Não há hoje um problema concreto que justifique dado de código/infra saindo do ambiente para uma API de terceiros, e o projeto é um produto de segurança (`docs/security/SECURITY.md`) — introduzir essa superfície sem necessidade real vai contra `docs/development/CONTRIBUTING.md` ("não adicionar tecnologias sem justificativa"). Se surgir uma necessidade real e isolada de teste de segurança autônomo (ex.: um pentest formal antes de um lançamento público), isso deve ser uma decisão própria, com ADR próprio — não parte do fluxo de codificação do dia a dia.
* **Cache de tarefas, CLI própria e logging customizado** não têm um problema concreto associado hoje (sem evidência de tarefas repetidas idênticas, os slash commands já cobrem a necessidade de CLI, e o transcript do Claude Code já serve de auditoria). Overengineering prematuro — revisitar apenas se um caso real aparecer.
* **Hooks automáticos** (pre/post-task) não foram configurados por falta de um gatilho concreto (ex.: "sempre rodar pytest depois de editar `backend/`"). Se isso for pedido no futuro, é uma spec própria via `.claude/settings.json`.

---

# Como usar

```text
/backend "adicionar endpoint X"
/security "revisar autenticação do endpoint Y"
/feature "implementar filtro de alertas por severidade"
```

Sem slash command, o Claude Code também pode rotear automaticamente para o agente certo com base na descrição da tarefa.
