# Deploy e operacao

Esta pasta concentra a documentacao de setup, producao, troubleshooting e historico operacional.

## Documentos principais

| Documento | Conteudo |
| --- | --- |
| `SETUP.md` | Preparacao do host, clone, variaveis e secrets. |
| `PRODUCTION.md` | Estrategia de deploy e operacao em producao. |
| `TROUBLESHOOTING.md` | Diagnostico e correcao de problemas. |
| `OPERATIONAL_HANDOFF_2026-06-28.md` | Consolidado do deploy real, incidentes, validacoes e runbook atual. |

## Referencias complementares

| Documento | Conteudo |
| --- | --- |
| `ORACLE_CLOUD.md` | Implantacao na Oracle Cloud. |
| `HTTPS.md` | DNS, Certbot e TLS. |
| `BOOTSTRAP.md` | Proposta de bootstrap versionado. |
| `CHANGELOG_DEPLOYMENT.md` | Diario de implantacao. |
| `POSTMORTEMS.md` | Incidentes e playbooks. |
| `DEPLOYMENT_HISTORY.md` | Historico detalhado do deploy. |
| `KNOWN_ISSUES.md` | Problemas conhecidos. |
| `LESSONS_LEARNED.md` | Licoes aprendidas. |
| `PRODUCTION_READINESS_REPORT.md` | Relatorio tecnico de readiness. |
| `WEEKLY_OPERATIONS.md` | Rotina semanal da EPIC 13: backup, restore, rollback, TLS, checks e Scout. |

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
