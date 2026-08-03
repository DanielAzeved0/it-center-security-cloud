# Deploy e operacao

Esta pasta concentra a documentacao de setup, producao, troubleshooting e historico operacional.

## Documentos principais

| Documento | Conteudo |
| --- | --- |
| `SETUP.md` | Preparacao do host, clone, variaveis e secrets. |
| `PRODUCTION.md` | Estrategia de deploy e operacao em producao. |
| `TROUBLESHOOTING.md` | Diagnostico e correcao de problemas. |
| `WEEKLY_OPERATIONS.md` | **Runbook operacional atual** (EPIC 13): backup, restore, rollback, TLS, checks e Scout, com registros ate 2026-07-28. |

## Qual arquivo usar para registrar o que

Esta pasta tem varios arquivos de historico que podem parecer redundantes; a diferenca e o proposito:

* **Aconteceu um incidente em produção?** Registre em `POSTMORTEMS.md` (narrativa do incidente + causa raiz + correcao).
* **Encontrou um problema ainda sem solucao definitiva?** Registre em `KNOWN_ISSUES.md` (problema em aberto, workaround se houver).
* **Aprendeu algo que deve mudar como o time trabalha?** Registre em `LESSONS_LEARNED.md` (retrospectiva, não é sobre um incidente especifico).
* **Fez um deploy (rotina ou extraordinario)?** Registre em `DEPLOYMENT_HISTORY.md` (linha do tempo cronologica). `CHANGELOG_DEPLOYMENT.md` esta congelado desde 2026-06-26 e não recebe novas entradas — use `DEPLOYMENT_HISTORY.md`.
* **Executou a rotina semanal (backup/restore/rollback/TLS/checks)?** Registre em `WEEKLY_OPERATIONS.md`.

## Referencias complementares

| Documento | Conteudo |
| --- | --- |
| `ORACLE_CLOUD.md` | Implantacao na Oracle Cloud. |
| `HTTPS.md` | DNS, Certbot e TLS. |
| `BOOTSTRAP.md` | Proposta de bootstrap versionado (ainda nao implementada). |
| `CHANGELOG_DEPLOYMENT.md` | Diario de implantacao inicial (congelado em 2026-06-26 — historico continua em `DEPLOYMENT_HISTORY.md`). |
| `POSTMORTEMS.md` | Incidentes e playbooks. |
| `DEPLOYMENT_HISTORY.md` | Historico cronologico completo do deploy. |
| `KNOWN_ISSUES.md` | Problemas conhecidos em aberto. |
| `LESSONS_LEARNED.md` | Licoes aprendidas (retrospectiva). |
| `PRODUCTION_READINESS_REPORT.md` | Relatorio tecnico de readiness. |
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
