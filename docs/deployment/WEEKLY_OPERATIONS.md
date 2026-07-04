# Rotina operacional semanal

Este runbook consolida a rotina minima da EPIC 13 para operar o ambiente publicado do IT Center Security Cloud.

Execute na VM:

```bash
cd /opt/itcenter/app/it-center-security-cloud
```

## 1. Checagem operacional

```bash
sh infra/scripts/ops-check.sh
```

O script valida:

* disco;
* memoria;
* `docker compose config`;
* containers `itcenter-postgres`, `itcenter-backend`, `itcenter-frontend` e `itcenter-nginx`;
* certificado TLS;
* existencia de backup recente.

Valores ajustaveis:

```bash
DISK_WARN_PERCENT=80
DISK_FAIL_PERCENT=90
MEM_WARN_MB=512
MEM_FAIL_MB=256
CERT_EXPIRY_WARN_DAYS=30
CERT_EXPIRY_FAIL_DAYS=7
BACKUP_MAX_AGE_HOURS=30
```

## 2. Backup periodico

Instalar agendamento diario via cron:

```bash
sudo sh infra/scripts/install-backup-cron.sh
```

Padrao:

```text
Horario: 02:15 UTC
Backups: /opt/itcenter/backups
Logs: /opt/itcenter/logs/postgres-backup.log
Retencao: 7 dias
```

Customizacao:

```bash
sudo BACKUP_HOUR=3 BACKUP_MINUTE=0 RETENTION_DAYS=14 sh infra/scripts/install-backup-cron.sh
```

Validar backup manual:

```bash
sh infra/scripts/backup.sh
ls -lh /opt/itcenter/backups
```

## 3. Restore controlado

Restore nunca deve ser executado automaticamente em producao.

Validacao recomendada em ambiente controlado:

```bash
ITCENTER_RESTORE_CONFIRM=YES sh infra/scripts/restore.sh /opt/itcenter/backups/itcenter-postgres-YYYYMMDDTHHMMSSZ.sql.gz
```

Antes de qualquer restore:

* confirmar janela operacional;
* gerar backup novo;
* confirmar que o arquivo de dump pertence ao ambiente correto;
* validar que o restore sera executado em ambiente controlado ou explicitamente autorizado.

## 4. Rollback

Antes de rollback:

```bash
sh infra/scripts/backup.sh
```

Validar rollback com Git ref conhecido:

```bash
sh infra/scripts/rollback.sh <git-ref-estavel>
```

O rollback preserva o volume `postgres_data`. Migrations precisam continuar retrocompativeis.

## 5. TLS

Validar renovacao sem alterar certificado real:

```bash
TLS_RENEW_DRY_RUN=1 sh infra/scripts/renew-tls.sh
```

Renovar quando necessario:

```bash
sh infra/scripts/renew-tls.sh
```

Depois, validar:

```bash
sh infra/scripts/ops-check.sh
curl -I https://itcenter-daniel.chickenkiller.com
```

## 6. Docker Scout

Antes de publicar novas imagens:

```bash
sh infra/scripts/docker-scout-gate.sh
```

O gate falha se Docker Scout encontrar CVEs `critical` ou `high` nas imagens configuradas.

## 7. Registro operacional

Registrar em `docs/deployment/DEPLOYMENT_HISTORY.md` quando houver:

* restore testado;
* rollback validado;
* renovacao TLS real;
* incidente;
* alteracao relevante de infraestrutura.

Registrar em `docs/deployment/POSTMORTEMS.md` somente quando houver incidente real.
