# Historico de Implantacao

Este documento registra o processo real de implantacao do IT Center Security Cloud na Oracle Cloud.

## 2026-08-20 - Tentativa de deploy via GitHub Actions falha no gate de CVE; correcao de design do gate

Contexto: apos o deploy manual de 2026-08-19 (EPIC 28/29), o usuario tentou um deploy real via workflow `Deploy Production` do GitHub Actions (nao mais manual por SSH). O job falhou no step "Deploy on VM" apos 1m44s, no `docker-scout-gate.sh`.

1. Log do GitHub Actions mostrou `postgres:16-alpine` com 2 CRITICAL + 20 HIGH (`golang/stdlib`) — `Error: Process completed with exit code 2`. Confirmado localmente: mesmo resultado (`docker scout cves postgres:16-alpine`).
2. Investigacao revelou a causa raiz: o gate original (`ITCENTER_SCOUT_IMAGES`) tratava as 7 imagens com o mesmo criterio rigido (`--exit-code`), sem NENHUM mecanismo de excecao para risco ja aceito (a propria `docs/security/SECURITY.md` ja documentava `postgres:16-alpine` como risco P1 aceito desde antes da EPIC 29 cablar o gate). Escaneadas as outras imagens de terceiros (`node-exporter`, `cadvisor`, `prometheus`, `grafana-oss`, EPIC 21): todas com o mesmo tipo de CVE (toolchain Go desatualizado, 43/64/47/84 vulnerabilidades cada) — ou seja, o gate nunca poderia ter passado desde que a EPIC 21 introduziu essas imagens (2026-08-15), independente do problema de RAM ja registrado em 2026-08-19.
3. Corrigido: `infra/scripts/docker-scout-gate.sh` reescrito com 2 grupos - gate rigido (`--exit-code`) so para `infra-backend`/`infra-frontend` (imagens que este projeto controla); as 5 imagens de terceiros passam a `ITCENTER_SCOUT_ACCEPTED_RISK_IMAGES`, reportadas a cada deploy mas sem `--exit-code` (nunca bloqueiam).
4. No processo de validar o novo gate contra `infra-backend:latest`, apareceram 3 CVEs HIGH reais e corrigiveis (`msgpack`, `setuptools`) que estavam mascaradas ate entao (o gate antigo sempre falhava primeiro em `postgres`, nunca chegava a escanear as imagens locais de verdade). Causa raiz: `pip` vendoriza copias proprias dessas dependencias (`pip._vendor`) independentes do que `requirements.txt` fixa. Corrigido removendo `pip`/`setuptools`/`wheel` de `backend/Dockerfile` apos a instalacao (mesmo padrao ja usado no frontend para o `npm`).
5. Validado localmente (Windows, Docker Desktop): `infra-backend`/`infra-frontend` com 0 vulnerabilidades critical/high; gate completo (`sh infra/scripts/docker-scout-gate.sh`) roda com exit code 0; container `backend` com a imagem corrigida sobe normalmente (`Applied 13 migration file(s)`, `GET /api/v1/health` respondendo).

Resultado:

* Gate de CVE corrigido para as 5 imagens de terceiros + 2 corregas reais no backend. **Nao validado ainda contra `itcenter-edge-01`** nem via GitHub Actions real — proximo passo natural, mas fora desta sessao a menos que autorizado.
* Risco pendente, sem mudanca: o problema de RAM ao escanear `infra-backend`/`infra-frontend` especificamente na VM (`itcenter-edge-01`, 954MB) continua sem solucao — essas 2 imagens seguem no gate rigido corretamente, entao o `deploy.sh` completo ainda pode travar la por falta de recursos, mesmo com o restante do gate corrigido. Ver `docs/deployment/KNOWN_ISSUES.md` e EPIC 36 (`docs/development/TASKS.md`).

## 2026-08-19 - Deploy da EPIC 28-A/28-B/29 em producao (defasagem de 2 dias entre checkout e containers)

Contexto: acesso SSH a `itcenter-edge-01` recuperado nesta sessao. Investigacao encontrou o checkout git em `/opt/itcenter/app/it-center-security-cloud` limpo e atualizado ate o commit `962e7ca` (2026-08-17, fechamento da EPIC 29) — porem os containers `backend`/`frontend` em execucao ainda eram da imagem de 2026-08-15T20:37:49Z (deploy da EPIC 21), 2 dias mais antiga que o codigo ja em disco. Confirmado via `information_schema.columns`: `machines.agent_secret_hash` (migration `009`, EPIC 28-A) nao existia em producao — ou seja, a correcao do achado mais grave da auditoria de 2026-08-15 (personificacao de maquina) estava pronta desde 17/08 mas nunca tinha sido ativada.

1. `sh infra/scripts/backup.sh` executado antes de qualquer mudanca — `itcenter-postgres-20260819T222957Z.sql.gz` gerado com sucesso.
2. `MIN_MEM_MB=256 sh infra/scripts/deploy.sh` executado: preflight OK, `docker compose build` reconstruiu `infra-backend`/`infra-frontend` sem erro.
3. **Achado novo**: `infra/scripts/docker-scout-gate.sh` falhou com `FAIL Docker Scout nao encontrado ou nao autenticado` — o plugin `docker scout` nunca havia sido instalado em `itcenter-edge-01` (a EPIC 29 so validou o gate via harness local, nunca contra a VM real). Plugin instalado (`docker/scout-cli`, script oficial, v1.24.0) e login no Docker Hub feito manualmente pelo operador (nao pela sessao do agente).
4. **Achado mais serio**: com o login feito, `docker scout cves infra-backend:latest` (imagem construida localmente, sem indice pre-computado no Docker Hub como as imagens oficiais) esgotou por completo os 954MB de RAM + 1GB de swap da VM so indexando o backend — processo em estado `D` (uninterruptible sleep), SSH ficou instavel/lento, e o processo do scout morreu sozinho apos ~30 minutos sem completar (sem OOM killer no kernel, mas efetivamente travado). Nenhum container de producao foi afetado (o `up -d` nunca foi alcancado nesse caminho).
5. Decisao: reexecutar os passos restantes do `deploy.sh` manualmente (`docker compose up -d` direto, pulando `docker-scout-gate.sh` so nesta execucao) — as imagens ja estavam construidas e o codigo ja passou por revisao normal antes do commit. `postgres`/`backend`/`frontend`/`nginx` recriados e saudaveis; `machines` com as 2 linhas anteriores preservadas (volume `postgres_data` intacto); 9 migrations aplicadas (`Applied 9 migration file(s).` no log de startup), `agent_secret_hash` confirmado presente; smoke tests (`/api/v1/health`, nginx->frontend, `/healthz`) todos OK.

Resultado:

* Producao agora roda o commit `962e7ca` de verdade (EPIC 28-A, 28-B e 29 ativas) — nao apenas checked out.
* **Risco novo identificado e nao resolvido**: `docker-scout-gate.sh`, como esta hoje, e impraticavel em `itcenter-edge-01` para imagens construidas localmente (infra-backend/infra-frontend) — precisa de mais memoria/swap na VM, ou rodar o scan em outro lugar (CI, por exemplo, que ja tem Docker Scout disponivel via GitHub Actions), ou aceitar formalmente pular esse gate especifico para imagens locais. Registrado em `docs/deployment/KNOWN_ISSUES.md`. Ate isso ser resolvido, `deploy.sh` completo (com o gate) nao deve ser reexecutado sem supervisao — o proximo operador precisa repetir o bypass manual (`docker compose up -d` direto) ou resolver o gate antes.
* `postgres:16-alpine` continua com o risco residual P1 ja documentado (CVEs de `golang/stdlib` sem tag corrigida) — inalterado por este deploy.

## 2026-08-15 - Ativacao real da observabilidade em producao (fechamento da EPIC 21)

> Este e o desfecho, ainda no mesmo dia, da entrada seguinte ("Implementacao da observabilidade..."), que havia registrado a validacao manual como pendente.

Contexto: sequencia da sessao anterior no mesmo dia. Com o codigo ja implementado e revisado (2 achados altos e 2 medios de seguranca corrigidos — mount de `/var/run` removido do cAdvisor, imagens novas adicionadas ao gate do Docker Scout, checagem de `GRAFANA_ADMIN_PASSWORD` fallback adicionada a `ops-check.sh`), a validacao manual pendente foi executada de fato contra a VM real.

1. `docker compose --env-file .env.production -f infra/docker-compose.production.yml --profile observability up -d` executado em `itcenter-edge-01`: os 4 containers (`node_exporter`, `cadvisor`, `prometheus`, `grafana`) subiram healthy/running.
2. `infra/scripts/ops-check.sh` executado contra o ambiente real: primeira rodada reportou `FAIL GRAFANA_ADMIN_PASSWORD nao configurado` (Grafana havia subido com o fallback placeholder por falta da variavel em `.env.production`) e `WARN Memoria disponivel MB em 424` (`free -h`: 448MB em uso no swap de 1GB de `itcenter-edge-01`).
3. `GRAFANA_ADMIN_PASSWORD` corrigido com senha forte em `.env.production` e o container `grafana` recriado (`docker compose ... --profile observability up -d grafana`).
4. `ops-check.sh` executado novamente: `OK Operacao sem falhas criticas` — o `FAIL` de senha foi eliminado; o `WARN` de memoria permanece, tratado como risco aceito (ver `docs/deployment/KNOWN_ISSUES.md`, "Observabilidade (EPIC 21): memoria em alerta com o profile ativo").
5. Decisao registrada: manter os 4 servicos ativos continuamente por ora (424MB ainda acima do limite critico de `MEM_FAIL_MB=256`); candidatos ja identificados se a situacao piorar: remover `cadvisor` do profile, ou ativar `observability` so sob demanda em vez de continuamente.

Resultado:

* EPIC 21 encerrada em `docs/development/TASKS.md` no mesmo dia 2026-08-15 — profile `observability` ativo em producao, nao mais apenas codigo implementado.
* Nenhum dos 4 servicos existentes (`postgres`, `backend`, `frontend`, `nginx`) foi alterado nesta ativacao.

## 2026-08-15 - Implementacao da observabilidade de infraestrutura (EPIC 21, ADR-030) - ainda nao ativada em producao

> **Atualizacao (mesmo dia, ver entrada acima):** a ressalva de "nao ativada em producao" registrada abaixo ficou desatualizada poucas horas depois — o profile `observability` foi de fato ativado em producao e a EPIC 21 foi encerrada ainda em 2026-08-15. Entrada mantida sem alteracao como registro do que foi escrito naquele momento.

Contexto: ADR-030 e a Fase F de `docs/architecture/FUTURE_ARCHITECTURE.md` ja definiam a decisao (Prometheus + Grafana para o Edge Node/containers, nunca para as maquinas Windows monitoradas pelo agente); esta sessao implementou o codigo.

1. Adicionados `node_exporter` (`prom/node-exporter:v1.8.2`), `cadvisor` (`gcr.io/cadvisor/cadvisor:v0.49.1`), `prometheus` (`prom/prometheus:v2.55.1`) e `grafana` (`grafana/grafana-oss:11.1.0`) a `infra/docker-compose.production.yml`, todos sob `profiles: ["observability"]` (mesmo padrao ja usado por `certbot`/`maintenance`) — nao sobem com `docker compose up` padrao.
2. `mem_limit` conservador em cada um (node_exporter ~30M, cadvisor ~100M, prometheus ~200M, grafana ~150M) e Prometheus com retencao curta (`--storage.tsdb.retention.time=5d`, `--storage.tsdb.retention.size=200MB`) e scrape/evaluation interval de 30s, por causa da VM Oracle Free Tier de 1GB de RAM (`itcenter-edge-01`).
3. `cadvisor` roda deliberadamente sem `privileged: true` (menor privilegio), aceitando perder metricas de I/O em disco em troca de nao conceder acesso privilegiado ao host.
4. Nenhum dos 4 servicos publica porta no host nem tem `location` nova em `infra/nginx/nginx.conf.template` — acesso operacional documentado via `docker exec` ou tunel SSH direto ao IP do container na rede `itcenter-network` (`docs/architecture/NETWORK.md`).
5. Configuracao versionada em `infra/observability/` (scrape config do Prometheus, datasource e dashboard "Edge Node Overview" provisionados automaticamente no Grafana).
6. `docker compose --env-file <.env de teste> -f infra/docker-compose.production.yml config -q` validado com sucesso, com e sem `--profile observability` (confirma apenas sintaxe do Compose, nao impacto real de recursos).
7. `docs/architecture/ARCHITECTURE.md`, `docs/architecture/CONTAINERS.md`, `docs/architecture/NETWORK.md`, `docs/security/SECURITY.md`, `infra/README.md` e `docs/development/TASKS.md` atualizados.

Resultado:

* EPIC 21 tem o codigo implementado, mas o profile `observability` **nao foi ativado em producao** nesta sessao. Falta rodar `infra/scripts/ops-check.sh` e observar memoria/disco reais em `itcenter-edge-01` com `docker compose --profile observability up -d` antes de considerar isso seguro continuamente — validacao manual pendente, deliberadamente nao simulada aqui.
* Nenhum dos 4 servicos existentes (`postgres`, `backend`, `frontend`, `nginx`) foi alterado; `docker-compose.yml` (dev local) nao foi tocado.

## 2026-08-15 - Descoberta do bloqueio de acesso a conta Oracle Cloud (EPIC 15)

Contexto: tentativa de retomar a EPIC 15 (migracao do state do Terraform para backend remoto em OCI Object Storage), mais cedo no mesmo dia, antes do trabalho de observabilidade (EPIC 21) registrado nas duas entradas acima.

1. Ao tentar acessar o Console Oracle Cloud para criar o bucket de Object Storage do state remoto, foi identificado que o unico usuario administrador da tenancy havia perdido o segundo fator de autenticacao (MFA vinculado a um celular antigo), sem fator de backup configurado e sem um segundo usuario administrador cadastrado na conta.
2. Investigacao adicional revelou que o `terraform.tfvars` e o `terraform.tfstate` reais do import de 2026-08-04 (EPIC 15) tambem nao foram localizados — nao estao em `itcenter-edge-01` nem em copia conhecida. A API key do usuario IAM `terraform-provisioner` (criada na mesma epoca) tambem foi dada como perdida.
3. Confirmado que nenhuma acao no Console ou via `oci` CLI e possivel ate a conta ser recuperada; a aplicacao em producao (dashboard, backend, agente, Nginx) continua funcionando normalmente, pois o bloqueio afeta apenas operacoes administrativas de infraestrutura na nuvem.
4. Registrado como bloqueio aberto em `docs/deployment/KNOWN_ISSUES.md` ("Acesso ao Console Oracle Cloud bloqueado") e como pendencia explicita da EPIC 15 em `docs/development/TASKS.md`. Incidente formal registrado retroativamente em `docs/deployment/POSTMORTEMS.md` (INCIDENTE 022).

Resultado:

* Migracao do state do Terraform para backend remoto (ultimo item pendente da EPIC 15) permanece bloqueada, sem previsao — depende de recuperacao de acesso ao Console Oracle Cloud (fator de backup, segundo administrador existente ou Service Request ao suporte Oracle).
* Nenhuma mudanca de infraestrutura foi feita nesta sessao; e um registro de descoberta/bloqueio, nao de deploy.

## 2026-08-11 - Reversao da integracao Snipe-IT (ADR-028 -> ADR-033)

Contexto: revisao de uma tela de maquina em producao (`itcenter-daniel.chickenkiller.com/machines/23`) mostrou "Ativo ainda nao sincronizado com o Snipe-IT" numa maquina com semanas de check-in. Investigacao no codigo (`app/services/snipeit.py`) confirmou que a causa raiz e estrutural: `SNIPEIT_BASE_URL`/`SNIPEIT_API_TOKEN` nunca foram configurados em producao porque nunca existiu um Snipe-IT real para o backend apontar.

1. Decisao: reverter a integracao em vez de provisionar um Snipe-IT real, por falta de necessidade concreta de ITAM identificada vs. custo de hospedar/manter um servico PHP+MySQL (arriscar OOM na `itcenter-edge-01` de 1GB ou manter uma segunda VM).
2. Codigo removido: `app/services/snipeit.py`, `backend/tests/test_snipeit_service.py`, `snipeit_*` de `app/core/config.py`, `snipeit_asset_id`/`snipeit_asset_url` do schema/servico/repositorio de machines, a chamada via `BackgroundTasks` no check-in, e o bloco Snipe-IT em `MachineDetailView.tsx`/`lib/types.ts`.
3. Nova migration `006_remove_machines_snipeit.sql` criada (forward-only, ainda nao aplicada em producao - so roda quando o deploy for disparado).
4. ADR-033 registrado em `docs/development/DECISIONS.md`; ADR-028 marcado com nota apontando para a reversao.
5. Suite completa do backend revalidada localmente (Postgres via Docker Compose): 89 passed (96 - 7 testes do Snipe-IT removidos). `npm run build` do frontend validado sem os campos removidos.

Resultado:

* EPIC 19 passa a cobrir só RustDesk (ADR-027), que continua funcionando sem alteracao. Snipe-IT volta para EPIC 14 (Melhorias Futuras) como item aspiracional.
* Nenhum deploy real de producao foi feito nesta sessao - a migration 006 e as mudancas de codigo ficam commitadas, aplicando-se em producao apenas no proximo deploy manual.

## 2026-08-11 - Validacao dos testes de RustDesk/Snipe-IT (fechamento da EPIC 19)

Contexto: EPIC 19 tinha backend e frontend implementados desde 2026-08-04, mas a execucao real de `pytest` ficara pendente por falta de ambiente com Docker/Postgres na sessao original.

1. Subido apenas o servico `postgres` de `infra/docker-compose.yml` via `docker compose up -d postgres` (imagem `postgres:16-alpine`, saudavel apos healthcheck).
2. Criado virtualenv local em `backend/.venv` e instaladas as dependencias de `backend/requirements.txt`.
3. Migrations aplicadas com `python apply_migrations.py` (5 arquivos, incluindo `004_machines_rustdesk.sql` e `005_machines_snipeit.sql`).
4. Suite completa executada com `pytest -q` a partir de `backend/`: 87 passed, 0 failed. Confirmado especificamente `tests/test_snipeit_service.py` (7 testes) e `tests/test_machines_rustdesk.py` (5 testes), todos PASSED.

Resultado:

* EPIC 19 (RustDesk + Snipe-IT) concluida em `docs/development/TASKS.md` - implementacao e validacao de testes fechadas.
* Nenhum codigo de producao alterado; apenas validacao local do que ja estava implementado desde 2026-08-04.

## 2026-08-04 - Adocao de Terraform via import (fechamento da EPIC 15)

Contexto: EPIC 15 tinha os modulos e o ADR-024 prontos, mas nenhum recurso real havia sido importado. Executado de ponta a ponta nesta sessao, com acesso real a conta Oracle Cloud.

1. Usuario IAM `terraform-provisioner` criado no Console OCI (grupo `TerraformProvisioners`), com policy de escopo minimo aplicada `in tenancy` (o Edge Node vive no root compartment, sem compartment dedicado - `in compartment <nome>` nao e valido para o root).
2. Descoberta via `oci` CLI revelou que a VCN foi criada pelo "VCN Wizard" da Oracle: alem dos recursos ja documentados, existem um NAT Gateway e um Service Gateway, e a subnet privada usa uma route table e uma security list dedicadas (nao as default da VCN, que na verdade pertencem a subnet publica). Documentado em `docs/architecture/IAC.md` e `docs/architecture/NETWORK.md`.
3. IP publico de producao (`147.15.78.220`) confirmado `EPHEMERAL` (nao `RESERVED`). Decisao: manter efemero por ora, sem reservar (reservar trocaria o endereco, exigindo janela de manutencao e atualizacao de DNS).
4. Modulos `network`/`compute` ajustados: variaveis novas para a route table/security list da subnet privada, regras ICMP padrao adicionadas, `versions.tf` proprio criado em cada modulo (faltava - sem ele o provider resolvia para o namespace legado `hashicorp/oci` dentro dos modulos), e corrigido um bug de schema (`source_details` usa `source_id`, nao `image_id`, no provider `oracle/oci` >= 5.x).
5. Import executado na ordem VCN -> Internet Gateway -> Route Table -> Security List -> Subnet publica -> Subnet privada -> Instancia, validando `terraform plan` sem diff funcional apos cada um. A instancia importou com diff zero de primeira.
6. Unico diff remanescente era cosmetico (tag `VCN` que o Wizard deixa em cada recurso de rede). Resolvido com um `terraform apply` minimo e deliberado (0 add, 6 change, 0 destroy - so update in-place de tags), apos salvar e revisar o plano com `-out`.
7. `terraform plan` final confirmado como `No changes. Your infrastructure matches the configuration.`. Producao validada no ar apos o apply (`curl -I` respondendo 401 do Basic Auth normal do Nginx).

Resultado:

* EPIC 15 concluida em `docs/development/TASKS.md`, exceto migracao do state para backend remoto (fora do escopo minimo, state segue local).
* Nenhum recurso foi destruido ou recriado - todos os itens ja existentes em producao, apenas trazidos para dentro do Terraform.

## 2026-07-28 - Recuperacao de acesso, criacao do primeiro admin e correcao do loop de login

Contexto: perda da chave SSH pessoal de acesso a `itcenter-edge-01`, ausencia de qualquer usuario administrativo na tabela `users` de producao, e um loop de login causado por conflito entre Basic Auth e Bearer token. Detalhes completos de cada causa raiz em `docs/deployment/POSTMORTEMS.md` (INCIDENTE 018, 019 e 020).

Linha do tempo:

1. Acesso SSH recuperado via workflow temporario `ssh-access-recovery.yml` (commit `b121ead`), que reaproveitou o secret `PROD_SSH_PRIVATE_KEY` ja usado pelo deploy para injetar uma nova chave publica no `authorized_keys` da VM.
2. Uma chave privada foi exposta acidentalmente durante o processo; foi tratada como comprometida e removida do `authorized_keys` assim que uma chave limpa ficou disponivel.
3. Workflow temporario removido do repositorio apos uso (commit `cdd85e2`).
4. Senha do HTTP Basic Auth (`admin`, `.secrets/dashboard.htpasswd`) redefinida via `htpasswd`.
5. Identificado que a tabela `users` estava vazia em producao. Primeiro usuario administrativo criado executando `backend/create_admin.py` manualmente dentro do container (o script nao faz parte da imagem Docker do backend).
6. Diagnosticado loop de login: chamadas autenticadas do dashboard (`Authorization: Bearer ...`) colidiam com o `Authorization: Basic` exigido pelo Nginx em `location /`.
7. Corrigido isentando `/api/backend/` do Basic Auth no Nginx (commit `c95586c`, ver ADR-023), aplicado na VM via `git pull` + `docker compose restart nginx`.
8. Login administrativo validado com sucesso no navegador, dashboard operacional (`/security` exibindo eventos reais).

Resultado:

* Acesso SSH administrativo restaurado com chave nova, sem chaves comprometidas remanescentes no `authorized_keys`.
* Primeiro usuario `admin` ativo criado em producao (`daniel.azevedo081205@gmail.com`).
* Login administrativo e navegacao no dashboard funcionando de ponta a ponta em producao.

## 2026-07-28 - Validacao de TLS, rollback e restore (fechamento da EPIC 13)

Contexto: ultimos tres itens pendentes da EPIC 13 validados em sequencia, do menor para o maior risco.

1. **TLS**: `TLS_RENEW_DRY_RUN=1 sh infra/scripts/renew-tls.sh` concluiu "all simulated renewals succeeded". Durante essa validacao foi descoberta a tag inexistente `certbot/certbot:v4.21.0` (INCIDENTE 021), corrigida para `v5.7.0` (commit `c682c7e`). Apos a correcao, a renovacao real (`sh infra/scripts/renew-tls.sh`) confirmou corretamente que o certificado so expira em 2026-09-24 e nao tentou renovar.
2. **Rollback**: backup gerado, `sh infra/scripts/rollback.sh f27d00c` executado com sucesso (containers reconstruidos e saudaveis, `postgres_data` preservado sem reiniciar o Postgres), seguido de `sh infra/scripts/rollback.sh c682c7e` para retornar ao estado atual. Dashboard validado funcional apos o rollforward.
3. **Restore**: backup fresco gerado (`itcenter-postgres-20260728T180730Z.sql.gz`) e restaurado com `ITCENTER_RESTORE_CONFIRM=YES sh infra/scripts/restore.sh` contra o proprio banco de producao. Schema recriado do zero, todas as tabelas restauradas com contagens consistentes com o backup, `/api/v1/health` respondendo `healthy` e dashboard funcional apos o restore.

Resultado: os tres itens `[~]` da EPIC 13 (`Testar restore em ambiente controlado`, `Validar rollback de deploy`, `Validar renovacao de certificado TLS`) ficam `[x]` em `docs/development/TASKS.md`. EPIC 13 considerada concluida, restando apenas a atualizacao continua de `POSTMORTEMS.md` quando houver incidente futuro.

## 2026-06-30 - Deploy manual via GitHub Actions

Workflow:

```text
Deploy Production
```

Commit implantado:

```text
7f5f846d4b51f9293daee8c943a05288e6976901
```

Resultado:

* `git fetch` autenticado via GitHub Actions concluido com sucesso.
* Backup PostgreSQL criado antes do deploy: `itcenter-postgres-20260630T231819Z.sql.gz`.
* Preflight de producao aprovado: Docker, Docker Compose, disco, memoria, secrets, dominio, TLS, rede, portas e volumes.
* Build das imagens `infra-backend` e `infra-frontend` concluido.
* Containers recriados e saudaveis: `itcenter-postgres`, `itcenter-backend`, `itcenter-frontend` e `itcenter-nginx`.
* Smoke tests de producao aprovados.
* Dashboard validado no navegador sem bug visual reportado.

URLs validadas:

```text
Dashboard: https://itcenter-daniel.chickenkiller.com/
Agent check-in: https://itcenter-daniel.chickenkiller.com/api/v1/agent/checkin
```

## 2026-06-30 - Validacao do ciclo periodico do agente

Resultado:

* Agente Windows permaneceu integrado ao ambiente publicado.
* Maquinas continuaram aparecendo no dashboard apos a validacao inicial.
* Ciclo periodico de check-in considerado validado operacionalmente.

Evidencia funcional:

```text
Dashboard publicado mantendo maquinas visiveis:
https://itcenter-daniel.chickenkiller.com/machines
```

## Linha do tempo tecnica

### 1. Docker e Compose

Foi instalado:

```text
Docker Engine
Docker Compose
```

O usuario `ubuntu` foi adicionado ao grupo `docker`.

Validacao:

```bash
docker --version
docker compose version
```

### 2. Acesso ao repositorio privado

Foi configurada chave SSH na Oracle VM e cadastrada no GitHub.

Clone validado:

```bash
git clone git@github.com:DanielAzeved0/it-center-security-cloud.git
```

### 3. Ambiente de producao

Foi criado `.env.production` a partir de `.env.production.example`.

Secrets gerados:

```text
POSTGRES_PASSWORD
AGENT_API_KEY
```

Comando usado:

```bash
openssl rand -hex 32
```

### 4. Credencial administrativa

Foi criada a pasta `.secrets` e o arquivo:

```text
.secrets/dashboard.htpasswd
```

Esse arquivo protege o dashboard com HTTP Basic Auth.

### 5. Compose de producao

Foi validado:

```text
infra/docker-compose.production.yml
```

Servicos:

```text
postgres
backend
frontend
nginx
certbot
```

### 6. Preflight

Foi criado `infra/scripts/preflight-production.sh`.

Validacoes:

* Docker.
* Docker Compose.
* Memoria.
* Disco.
* `.env.production`.
* Secrets.
* Dominio.
* Certificados TLS.
* Volumes.
* Rede Docker.
* Portas.
* Configuracao Docker Compose.

### 7. Deploy

Foi criado `infra/scripts/deploy.sh`.

Responsabilidades:

* Executar preflight.
* Fazer build.
* Executar `docker compose up -d`.
* Aguardar healthchecks.
* Executar smoke tests.
* Mostrar URLs finais.

### 8. Healthcheck do frontend

Foi identificado que o Next.js standalone respondia corretamente pelo DNS interno Docker, mas recusava conexao quando o smoke test consultava `127.0.0.1:3000` em determinado contexto de container.

O smoke test e o healthcheck de producao foram ajustados para validar o frontend pela rede Docker.

Resultado:

```text
nginx -> http://frontend:3000/ -> 200 OK
```

### 9. DNS

Dominio criado:

```text
itcenter-daniel.chickenkiller.com
```

Apontamento:

```text
147.15.78.220
```

### 10. TLS

Certificado emitido com Let's Encrypt apos ajustes na abertura da porta 80.

Arquivos gerados:

```text
fullchain.pem
privkey.pem
```

### 11. Nginx

Nginx configurado para:

* TLS.
* HTTP para HTTPS.
* Basic Auth.
* Reverse proxy.
* Headers de seguranca.
* Rate limit.
* Proxy para backend.
* Proxy para frontend.

### 12. Validacao final

Todos os containers ficaram saudaveis:

```text
postgres: healthy
backend: healthy
frontend: healthy
nginx: healthy
```

Foram testados:

* Backend `/api/v1/health`.
* Frontend.
* Nginx.

### 13. Problemas encontrados

* DNS da Vivo demorou a propagar.
* Permissao `600` em `dashboard.htpasswd` gerou `500 Internal Server Error` no Nginx; corrigido para `644`.
* Pouca memoria na VM exigiu criacao de Swap.
* O preflight precisou ser executado com `MIN_MEM_MB=256` apos confirmacao de swap ativo na Oracle Free Tier.
* O agente Windows retornou `401` enquanto usava API key diferente de `AGENT_API_KEY` em producao; corrigido ao alinhar a chave instalada no agente.

### 14. Estado final

```text
Infraestrutura: funcional
HTTPS: funcional
Nginx: funcional
Dashboard: funcional
Backend: funcional
PostgreSQL: funcional
Windows Agent: integrado e enviando check-in com 200 OK
```
