# Rotina operacional semanal

Este runbook consolida a rotina minima da EPIC 13 para operar o ambiente publicado do IT Center Security Cloud.

Execute na VM:

```bash
cd /opt/itcenter/app/it-center-security-cloud
```

## 1. Secrets obrigatorios

Antes de deploy, valide sem imprimir os valores reais:

```bash
grep '^AGENT_API_KEY=' .env.production | sed 's/=.*/=<definida>/'
grep '^AUTH_TOKEN_SECRET=' .env.production | sed 's/=.*/=<definida>/'
grep '^POSTGRES_PASSWORD=' .env.production | sed 's/=.*/=<definida>/'
grep '^DATABASE_URL=' .env.production | sed 's#://.*@#://<credenciais>@#'
grep '^AUTH_TOKEN_EXPIRATION_MINUTES=' .env.production
```

Se `AUTH_TOKEN_SECRET` estiver ausente, gerar e gravar na VM:

```bash
AUTH_SECRET=$(openssl rand -hex 32)

if grep -q '^AUTH_TOKEN_SECRET=' .env.production; then
  sed -i "s/^AUTH_TOKEN_SECRET=.*/AUTH_TOKEN_SECRET=$AUTH_SECRET/" .env.production
else
  printf '\nAUTH_TOKEN_SECRET=%s\n' "$AUTH_SECRET" >> .env.production
fi

grep -q '^AUTH_TOKEN_EXPIRATION_MINUTES=' .env.production || printf 'AUTH_TOKEN_EXPIRATION_MINUTES=60\n' >> .env.production
chmod 600 .env.production
```

## 2. Checagem operacional

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

## 3. Backup periodico

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

## 4. Restore controlado

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

## 5. Rollback

Antes de rollback:

```bash
sh infra/scripts/backup.sh
```

Validar rollback com Git ref conhecido:

```bash
sh infra/scripts/rollback.sh <git-ref-estavel>
```

O rollback preserva o volume `postgres_data`. Migrations precisam continuar retrocompativeis.

## 6. TLS

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

## 7. Docker Scout

Antes de publicar novas imagens:

```bash
sh infra/scripts/docker-scout-gate.sh
```

O gate falha se Docker Scout encontrar CVEs `critical` ou `high` nas imagens configuradas.

**Atencao (achado de 2026-08-19, EPIC 36):** rodar isso contra `infra-backend`/`infra-frontend` (imagens construidas localmente, sem indice pre-computado no Docker Hub como as imagens oficiais) ja travou `itcenter-edge-01` por ~30 minutos esgotando RAM+swap. Antes de rodar manualmente contra essas 2 imagens na VM, ver `docs/deployment/KNOWN_ISSUES.md` ("Docker Scout gate (EPIC 29) impraticavel...") — a EPIC 36 ainda nao tem correcao aplicada.

## 8. Auditoria de dependencias do frontend

O job `frontend` do CI (`.github/workflows/ci.yml`) roda `npm audit --audit-level=high` a cada PR/push em `main`, com acesso direto ao registry (sem o proxy corporativo que bloqueia esse comando no ambiente local). Consultar o resultado do workflow antes de mesclar quando houver alerta.

## 9. Registro operacional

Registrar em `docs/deployment/DEPLOYMENT_HISTORY.md` quando houver:

* restore testado;
* rollback validado;
* renovacao TLS real;
* incidente;
* alteracao relevante de infraestrutura.

Registrar em `docs/deployment/POSTMORTEMS.md` somente quando houver incidente real.

## 10. Verificar defasagem entre checkout e containers rodando

Nenhum item desta rotina, nem `infra/scripts/ops-check.sh`, confere se o codigo que os containers `backend`/`frontend` estao servindo de fato bate com o commit do checkout git em `/opt/itcenter/app/it-center-security-cloud` — foi exatamente essa lacuna que deixou uma defasagem de 2 dias passar despercebida ate 2026-08-19 (ver `docs/deployment/DEPLOYMENT_HISTORY.md`, entrada de 2026-08-19). Ate existir uma checagem automatizada, conferir manualmente:

```bash
cd /opt/itcenter/app/it-center-security-cloud
git log -1 --format='%H %ci %s'
docker inspect itcenter-backend --format 'Image Created: {{.Created}}'
docker inspect itcenter-frontend --format 'Image Created: {{.Created}}'
```

Se a data do commit for mais recente que a data de criacao das imagens, os containers estao rodando codigo desatualizado frente ao que ja foi commitado/revisado — rodar `sh infra/scripts/deploy.sh` (ou investigar por que um deploy anterior nao completou, como aconteceu com o gate do Scout na EPIC 36).
