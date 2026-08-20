# Specs (Spec-Driven Development)

Esta pasta guarda as specs geradas pelo skill `/sdd` (`docs/development/AI_WORKFLOW.md`) para features/EPICs de nivel de rigor 3-4 (arquitetural/critico) — research, especificacao, plano tecnico e verificacao, antes e durante a implementacao.

Convencao: `docs/specs/<feature-name>/{research.md,spec.md,plan.md,verification.md}`. Nem toda EPIC gera uma pasta aqui — so as que passam pelo fluxo formal de spec (ver os niveis de rigor no skill). EPICs mais simples continuam documentadas direto em `docs/development/TASKS.md`.

## Specs existentes

| Pasta | EPIC | Status |
| --- | --- | --- |
| `epic-22-agent-auto-update/` | EPIC 22 — Auto-atualizacao do Agente Windows (ADR-032) | VERIFIED (ver `verification.md`) |
| `epic-31-agent-windows-resilience/` | EPIC 31 — Resiliencia do Agente Windows | SPECIFIED, aguardando aprovacao (2 perguntas em aberto no proprio `spec.md`) |
| `epic-37-documentation-audit-fixes/` | EPIC 37 — Correcao de Achados da Auditoria de Documentacao | VERIFIED (Trilha 1/Nginx so localmente, nao deployada em producao) |

Cada spec tem seu proprio campo `Status` no cabecalho (`DRAFT -> RESEARCHED -> SPECIFIED -> REVIEWED -> APPROVED -> IMPLEMENTING -> VERIFIED -> COMPLETED`) — essa tabela e so um atalho, o estado oficial de cada uma vive no arquivo `spec.md` correspondente.

Nao versionar nada sensivel aqui — specs sao planejamento tecnico, nao devem conter segredos/credenciais.
