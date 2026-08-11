# Deploy e operacao

Esta pasta concentra a documentacao de setup, producao, troubleshooting e historico operacional.

## Documentos principais

| Documento | Conteudo |
| --- | --- |
| `SETUP.md` | Preparacao do host, clone, variaveis e secrets. |
| `PRODUCTION.md` | Estrategia de deploy e operacao em producao. |
| `TROUBLESHOOTING.md` | Diagnostico e correcao de problemas. |
| `WEEKLY_OPERATIONS.md` | **Runbook operacional atual** (EPIC 13): backup, restore, rollback, TLS, checks e Scout. Documento evergreen, sem entradas datadas — o historico cronologico de quando cada rotina foi executada fica em `DEPLOYMENT_HISTORY.md` e `POSTMORTEMS.md`. |

## Qual arquivo usar para registrar o que

Esta pasta tem varios arquivos de historico que podem parecer redundantes; a diferenca e o proposito:

* **Aconteceu um incidente em produção?** Registre em `POSTMORTEMS.md` (narrativa do incidente + causa raiz + correcao).
* **Encontrou um problema ainda sem solucao definitiva?** Registre em `KNOWN_ISSUES.md` (problema em aberto, workaround se houver).
* **Aprendeu algo que deve mudar como o time trabalha?** Registre em `LESSONS_LEARNED.md` (retrospectiva, não é sobre um incidente especifico).
* **Fez um deploy (rotina ou extraordinario)?** Registre em `DEPLOYMENT_HISTORY.md` (linha do tempo cronologica). `CHANGELOG_DEPLOYMENT.md` esta congelado desde 2026-06-26 e não recebe novas entradas — use `DEPLOYMENT_HISTORY.md`.
* **Executou a rotina semanal (backup/restore/rollback/TLS/checks)?** Registre em `WEEKLY_OPERATIONS.md`.
* **Fechou uma EPIC com dependencia de infraestrutura real ou que ficou pendente de validacao com ambiente externo (Terraform/OCI, credenciais externas, Docker/Postgres local usado so para desbloquear um teste que dependia disso)?** Registre tambem em `DEPLOYMENT_HISTORY.md`, mesmo sem deploy formal em producao. Uma validacao puramente local que nao dependia de nenhum ambiente externo (ex.: `npm run build`/`pytest` sem pendencia previa) fica só em `docs/development/TASKS.md`.

## Referencias complementares

| Documento | Conteudo |
| --- | --- |
| `ORACLE_CLOUD.md` | Implantacao na Oracle Cloud. |
| `HTTPS.md` | DNS, Certbot e TLS. |
| `BOOTSTRAP.md` | Proposta de bootstrap versionado (ainda nao implementada). |
| `infra/terraform/README.md` | Modulos Terraform da camada abaixo do SO (ADR-024), adotados via `terraform import`. |
| `docs/architecture/IAC.md` | Decisao e escopo do Terraform na infraestrutura (VCN, subnets, security list, instancia). |
| `CHANGELOG_DEPLOYMENT.md` | Diario de implantacao inicial (congelado em 2026-06-26 — historico continua em `DEPLOYMENT_HISTORY.md`). |
| `POSTMORTEMS.md` | Incidentes e playbooks. |
| `DEPLOYMENT_HISTORY.md` | Historico cronologico completo do deploy. |
| `KNOWN_ISSUES.md` | Problemas conhecidos em aberto. |
| `LESSONS_LEARNED.md` | Licoes aprendidas (retrospectiva). |
| `PRODUCTION_READINESS_REPORT.md` | Relatorio tecnico de readiness (snapshot de ~2026-06-25, nao e guia vivo). |
| `OPERATIONAL_HANDOFF_2026-06-28.md` | Snapshot historico do deploy/incidentes/validacoes ate 2026-06-28 — para o runbook atual, use `WEEKLY_OPERATIONS.md`. |

## Comandos principais

```bash
cd /opt/itcenter/app/it-center-security-cloud
sh infra/scripts/preflight-production.sh
sh infra/scripts/deploy.sh
sh infra/scripts/backup.sh
sh infra/scripts/ops-check.sh
```

## Ambiente atual

```text
Dominio: itcenter-daniel.chickenkiller.com
IP publico: 147.15.78.220
Cloud: Oracle Cloud
Sistema: Ubuntu 24.04 LTS
Rede Docker: itcenter-network
```
