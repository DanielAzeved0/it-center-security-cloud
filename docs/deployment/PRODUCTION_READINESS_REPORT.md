# Relatorio tecnico de production readiness

> Snapshot de 2026-06-25/26 (ADR-015, criação dos scripts de deploy). Não é atualizado continuamente — para o estado/roadmap atual, ver `docs/development/TASKS.md` e `docs/development/ROADMAP.md`.

## Escopo

Esta refatoracao prepara a infraestrutura de producao do IT Center Security Cloud para operar com mais seguranca, reprodutibilidade e manutencao, sem alterar funcionalidades da aplicacao, endpoints da API, contratos do frontend ou comportamento do agente Windows.

## Mudancas realizadas

### Backend Dockerfile

* Migrou a imagem base de `python:3.14-alpine` para `python:3.13-alpine`.
* Manteve instalacao de dependencias antes da copia do codigo para preservar cache.
* Adicionou usuario nao-root para execucao da API.
* Adicionou comentarios explicando cada etapa.

Justificativa: as dependencias atuais (`fastapi`, `uvicorn`, `psycopg`) e o codigo do backend nao exigem Python 3.14. Python 3.13 reduz risco de usar uma base mais nova sem necessidade funcional.

Impacto esperado: imagem mais conservadora, pequena e com menor privilegio em runtime.

### Frontend Dockerfile

* Habilitou `output: "standalone"` no Next.js.
* Ajustou a imagem final para copiar apenas `.next/standalone`, `.next/static` e `public`.
* Removeu dependencia do `node_modules` completo em runtime.
* Manteve multi-stage build e o patch de seguranca existente do `picomatch`.

Justificativa: o standalone output reduz dependencias carregadas no container final e preserva o comportamento do Next.js em producao.

Impacto esperado: menor superficie de ataque e menor tamanho final da imagem.

### Docker Compose de producao

* Backend passou a usar healthcheck com `wget` em vez de comando Python.
* Frontend e Nginx receberam healthchecks.
* Nginx agora depende do frontend healthy.
* Servicos receberam `security_opt: no-new-privileges:true`.
* Rede `itcenter-network` e volume `postgres_data` permanecem nomeados explicitamente.

Justificativa: melhorar recuperacao apos reboot da VM e reduzir complexidade operacional dos healthchecks.

Impacto esperado: inicializacao mais previsivel e melhor diagnostico com `docker compose ps`.

### Nginx

* Adicionado `server_tokens off`.
* Adicionado endpoint `/healthz` para healthcheck interno.
* Mantido HTTP/2 em TLS.
* Reforcados headers de seguranca.
* Adicionados timeouts de cliente/proxy.
* Configurados proxy buffers.
* Ocultados headers desnecessarios de upstream quando possivel.
* Adicionados headers de cache privado para assets estaticos.

Justificativa: hardening do ponto publico sem alterar rotas da aplicacao.

Impacto esperado: menor exposicao de metadados, melhor comportamento sob conexoes lentas e base mais adequada para monitoramento futuro.

### Scripts operacionais

Criados:

* `infra/scripts/preflight-production.sh`
* `infra/scripts/deploy.sh`
* `infra/scripts/rollback.sh`
* `infra/scripts/backup.sh`
* `infra/scripts/restore.sh`

Justificativa: substituir sequencias manuais por comandos versionados, auditaveis e repetiveis.

Impacto esperado: deploys mais seguros, rollback mais rapido e backup/restore padronizados.

### Documentacao

Atualizados:

* `docs/architecture/ARCHITECTURE.md`
* `docs/deployment/PRODUCTION.md`
* `docs/development/DECISIONS.md`
* `infra/README.md`
* `README.md`

Documentado:

* Edge Node.
* Infrastructure Layer.
* Platform Layer.
* Application Layer.
* Data Layer.
* Security Layer.
* Fluxo de deploy.
* Fluxo de rollback.
* Fluxo de backup e restore.
* Estrutura `/opt/itcenter`.

## Estrutura operacional oficial

```text
/opt/itcenter/
|-- app/
|-- backups/
|-- configs/
|-- runtime/
|-- scripts/
|-- secrets/
|-- logs/
`-- bin/
```

## Riscos identificados

* `rollback.sh` usa Git ref e nao desfaz migrations de schema. Migrations devem ser retrocompativeis.
* `restore.sh` sobrescreve o schema `public`; exige `ITCENTER_RESTORE_CONFIRM=YES`, mas ainda deve ser usado apenas com janela operacional.
* O preflight exige TLS real; em ambiente inicial sem certificado, o Certbot deve ser executado antes do deploy final.
* O backend ainda instala `pytest` porque `requirements.txt` mistura dependencias de runtime e teste.
* PostgreSQL continua em container no mesmo Edge Node no MVP; isso e aceitavel para custo zero, mas nao e alta disponibilidade.

## Validacoes recomendadas

Na VM:

```bash
sh infra/scripts/preflight-production.sh
sh infra/scripts/deploy.sh
sh infra/scripts/backup.sh
docker compose --env-file .env.production -f infra/docker-compose.production.yml ps
```

Validar externamente:

```bash
curl --fail --user admin:SENHA_FORTE_AQUI https://SEU_DOMINIO/
```

## Evolucoes futuras

* Separar `requirements.txt` em runtime e dev/test para reduzir a imagem do backend.
* Adicionar CI/CD com build, testes, Docker Scout e publish controlado. **Já implementado** desde então (`.github/workflows/ci.yml` e `deploy-production.yml`).
* Adicionar Prometheus para metricas. **Já tem planejamento formal**: EPIC 21 / ADR-030 (`docs/development/DECISIONS.md`).
* Adicionar Loki/Promtail para logs.
* Adicionar Grafana para dashboards operacionais. **Já tem planejamento formal**: EPIC 21 / ADR-030, junto com Prometheus.
* Adicionar Wazuh para telemetria defensiva avancada. Continua como EPIC 14, fora do escopo do MVP, sem ADR ainda.
* Adicionar alertas de disco, memoria, containers unhealthy e expiracao de certificado.
* Avaliar PostgreSQL gerenciado ou instancia privada dedicada quando o MVP crescer.
* Avaliar Kubernetes apenas quando houver necessidade real de escala, alta disponibilidade ou multiplos ambientes. **Atualizado**: hoje existe regra dura do projeto proibindo Kubernetes (e RabbitMQ/Kafka/Redis/microsservicos/Elasticsearch) no MVP a menos que exista decisao formal em ADR (`docs/development/CONTRIBUTING.md`) — nao e mais uma avaliacao em aberto.
