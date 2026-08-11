# Handoff operacional - 2026-06-28

> **Snapshot historico do deploy/incidentes/validacoes ate 2026-06-28.** Nao e atualizado continuamente — para o runbook operacional atual, ver `docs/deployment/WEEKLY_OPERATIONS.md`, `docs/deployment/KNOWN_ISSUES.md` e `docs/agent/INSTALLATION.md`.

Este documento consolida o que foi feito, validado e corrigido durante a publicacao do IT Center Security Cloud e a integracao inicial do Windows Agent.

Ele deve ser usado como referencia rapida para reproduzir o deploy, diagnosticar falhas parecidas e instalar novos agentes sem repetir o ciclo de tentativa e erro.

## Estado atual

```text
Status geral: operacional
Dominio: itcenter-daniel.chickenkiller.com
IP publico: 147.15.78.220
Cloud: Oracle Cloud
VM: itcenter-edge-01
Sistema: Ubuntu Server 24.04 LTS
Runtime: Docker Engine
Orquestracao: Docker Compose
Rede Docker: itcenter-network
Repositorio na VM: /opt/itcenter/app/it-center-security-cloud
Entrada publica: Nginx nas portas 80 e 443
Dashboard: protegido por HTTP Basic Auth
Agent check-in: protegido por X-Agent-Api-Key
```

Containers esperados:

```text
itcenter-postgres   PostgreSQL
itcenter-backend    FastAPI
itcenter-frontend   Next.js standalone
itcenter-nginx      Reverse proxy HTTPS
```

Estado validado:

```text
PostgreSQL: healthy
Backend: healthy
Frontend: healthy
Nginx: healthy
TLS: valido
Dashboard: HTTP 200 com Basic Auth
Agent check-in: HTTP 200 quando a maquina resolve o dominio e usa a API key correta
```

## Arquivos de producao

Na VM:

```text
/opt/itcenter/app/it-center-security-cloud/.env.production
/opt/itcenter/app/it-center-security-cloud/.secrets/dashboard.htpasswd
/etc/letsencrypt/live/itcenter-daniel.chickenkiller.com/fullchain.pem
/etc/letsencrypt/live/itcenter-daniel.chickenkiller.com/privkey.pem
```

Nao registrar valores de `POSTGRES_PASSWORD`, `DATABASE_URL`, `AGENT_API_KEY`, `AUTH_TOKEN_SECRET` ou senha do dashboard em commits, logs, issues ou documentacao.

## Variaveis obrigatorias

`.env.production` deve conter:

```env
APP_ENV=production
DOMAIN_NAME=itcenter-daniel.chickenkiller.com
POSTGRES_DB=it_center_security_cloud
POSTGRES_USER=itcenter
POSTGRES_PASSWORD=<secret>
DATABASE_URL=postgresql://itcenter:<secret>@postgres:5432/it_center_security_cloud
AGENT_API_KEY=<secret>
AUTH_TOKEN_SECRET=<secret>
AUTH_TOKEN_EXPIRATION_MINUTES=60
ITCENTER_API_BASE_URL=http://backend:8000
NEXT_PUBLIC_API_BASE_URL=/api/backend
```

Validacao sem expor segredos:

```bash
cd /opt/itcenter/app/it-center-security-cloud

grep -E '^(APP_ENV|DOMAIN_NAME|POSTGRES_DB|POSTGRES_USER|ITCENTER_API_BASE_URL|NEXT_PUBLIC_API_BASE_URL)=' .env.production
grep '^AGENT_API_KEY=' .env.production | sed 's/=.*/=<definida>/'
grep '^AUTH_TOKEN_SECRET=' .env.production | sed 's/=.*/=<definida>/'
grep '^POSTGRES_PASSWORD=' .env.production | sed 's/=.*/=<definida>/'
grep '^DATABASE_URL=' .env.production | sed 's#://.*@#://<credenciais>@#'
```

## Deploy validado

Em VM pequena da Oracle Free Tier, foi necessario ativar swap e reduzir o limite minimo do preflight para memoria disponivel real.

Comando usado:

```bash
cd /opt/itcenter/app/it-center-security-cloud
MIN_MEM_MB=256 sh infra/scripts/deploy.sh
```

O `deploy.sh` executa:

```text
1. preflight-production.sh
2. docker compose config -q
3. docker compose build
4. docker compose up -d
5. espera healthchecks
6. smoke tests internos
```

Smoke tests corretos:

```bash
docker compose --env-file .env.production -f infra/docker-compose.production.yml exec -T backend wget -q -O /dev/null http://127.0.0.1:8000/api/v1/health
docker compose --env-file .env.production -f infra/docker-compose.production.yml exec -T nginx wget -q -O /dev/null http://frontend:3000/
docker compose --env-file .env.production -f infra/docker-compose.production.yml exec -T nginx wget -q -O /dev/null http://127.0.0.1/healthz
```

O frontend deve ser testado pela rede Docker com `frontend:3000`, a partir do Nginx. O teste antigo em `127.0.0.1:3000` dentro do contexto errado podia retornar `Connection refused` mesmo com o dashboard funcional.

## Validacoes externas

Health do Nginx:

```bash
curl -k -i https://itcenter-daniel.chickenkiller.com/healthz
```

Dashboard sem credencial deve pedir Basic Auth:

```bash
curl -k -i https://itcenter-daniel.chickenkiller.com/
```

Dashboard com credencial deve retornar `HTTP/2 200`:

```bash
curl -k -i -u admin:'<senha-do-dashboard>' https://itcenter-daniel.chickenkiller.com/
```

## Incidentes resolvidos

### DNS local nao resolvia o dominio

Sintoma no Windows:

```text
O nome remoto nao pode ser resolvido: 'itcenter-daniel.chickenkiller.com'
```

Diagnostico:

```powershell
nslookup itcenter-daniel.chickenkiller.com
nslookup itcenter-daniel.chickenkiller.com 1.1.1.1
nslookup itcenter-daniel.chickenkiller.com 8.8.8.8
Test-NetConnection itcenter-daniel.chickenkiller.com -Port 443
```

Resultado observado:

```text
DNS da Vivo retornava NXDOMAIN.
Cloudflare e Google resolviam corretamente para 147.15.78.220.
```

Correcao pontual usada:

```text
hosts no Windows apontando para 147.15.78.220
```

Decisao operacional:

* Nao usar `hosts` como estrategia de distribuicao.
* Corrigir DNS no roteador/DHCP ou migrar para dominio gerenciado de forma mais confiavel.
* O instalador agora bloqueia instalacao quando DNS/TCP/health check falham.

### Basic Auth retornava 500

Sintoma:

```text
500 Internal Server Error
open() "/etc/nginx/auth/dashboard.htpasswd" failed (13: Permission denied)
```

Causa:

```text
.secrets/dashboard.htpasswd estava com permissao 600 no host e o worker do Nginx nao conseguia ler o arquivo montado no container.
```

Correcao:

```bash
chmod 644 .secrets/dashboard.htpasswd
docker compose --env-file .env.production -f infra/docker-compose.production.yml restart nginx
```

Validacao:

```bash
curl -k -i -u admin:'<senha-do-dashboard>' https://itcenter-daniel.chickenkiller.com/
```

### Preflight falhava por memoria

Sintoma:

```text
FAIL Memoria disponivel insuficiente
```

Contexto:

```text
VM Oracle Free Tier com pouca RAM disponivel.
Swap ativo, mas o preflight mede MemAvailable e nao soma swap.
```

Correcao:

```bash
sudo rm -f /swapfile
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

Deploy em VM pequena:

```bash
MIN_MEM_MB=256 sh infra/scripts/deploy.sh
```

### Agente retornava 401

Sintoma:

```text
O servidor remoto retornou um erro: (401) Nao Autorizado.
```

Causa:

```text
API key instalada no agente diferente de AGENT_API_KEY em producao.
```

Validacao na VPS:

```bash
ENV_KEY=$(grep '^AGENT_API_KEY=' .env.production | cut -d= -f2-)
CONTAINER_KEY=$(docker exec itcenter-backend printenv AGENT_API_KEY)
test "$ENV_KEY" = "$CONTAINER_KEY" && echo "AGENT_API_KEY igual" || echo "AGENT_API_KEY diferente"
```

Correcao:

```text
Reinstalar ou atualizar config.json do agente com a API key real de producao.
```

### Smoke test do frontend falhava

Sintoma:

```text
wget: can't connect to remote host (127.0.0.1): Connection refused
```

Causa:

```text
Teste apontava para 127.0.0.1:3000 no contexto errado. O frontend respondia corretamente pela rede Docker em frontend:3000.
```

Correcao versionada:

```text
infra/scripts/deploy.sh
infra/docker-compose.production.yml
```

## Windows Agent

Arquivos necessarios para distribuir o agente:

```text
agent-windows/install-agent.ps1
agent-windows/itcenter-agent.ps1
agent-windows/uninstall-agent.ps1
```

Nao e necessario clonar o repositorio inteiro em cada PC. Basta copiar a pasta `agent-windows`.

Instalacao em outro PC, PowerShell como Administrador:

```powershell
cd "C:\Caminho\Para\agent-windows"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install-agent.ps1 `
  -ServerUrl "https://itcenter-daniel.chickenkiller.com" `
  -AgentApiKey "<AGENT_API_KEY_DE_PRODUCAO>" `
  -CheckinIntervalMinutes 5 `
  -Force
```

O instalador agora faz preflight:

```text
1. DNS do dominio.
2. Conexao TCP na porta 443.
3. Health check /healthz.
```

Se falhar, ele nao instala. Isso evita agentes instalados sem conectividade acumulando cache.

Bypass apenas quando offline for intencional:

```powershell
-SkipConnectivityCheck
```

Check-in manual:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Program Files\ITCenterAgent\itcenter-agent.ps1" `
  -ConfigPath "C:\Program Files\ITCenterAgent\config.json"
```

Validar log:

```powershell
Get-Content "C:\Program Files\ITCenterAgent\logs\itcenter-agent.log" -Tail 80
```

Sucesso esperado:

```text
Check-in sent successfully.
```

Cache deve estar vazio ou reduzindo:

```powershell
Get-ChildItem "C:\Program Files\ITCenterAgent\cache" -Filter "checkin-*.json"
```

Desinstalacao completa:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Program Files\ITCenterAgent\uninstall-agent.ps1" -RemoveFiles -RemoveData
```

Validar remocao:

```powershell
Get-ScheduledTask -TaskName "ITCenterAgent" -ErrorAction SilentlyContinue
Test-Path "C:\Program Files\ITCenterAgent"
```

## Mudancas versionadas neste ciclo

Infra:

```text
infra/scripts/deploy.sh
infra/docker-compose.production.yml
```

Agente:

```text
agent-windows/install-agent.ps1
agent-windows/README.md
docs/agent/INSTALLATION.md
docs/agent/README.md
```

Documentacao:

```text
README.md
infra/README.md
docs/deployment/README.md
docs/deployment/PRODUCTION.md
docs/deployment/TROUBLESHOOTING.md
docs/deployment/DEPLOYMENT_HISTORY.md
docs/deployment/LESSONS_LEARNED.md
docs/deployment/KNOWN_ISSUES.md
docs/deployment/POSTMORTEMS.md
docs/deployment/OPERATIONAL_HANDOFF_2026-06-28.md
```

## Validacoes executadas localmente

```text
install-agent.ps1 syntax ok
Agent tests passed.
git diff --check sem erros
```

## Riscos remanescentes

### Dominio gratuito e DNS de provedor

`chickenkiller.com` funcionou em resolvers publicos, mas falhou no DNS da Vivo em uma maquina monitorada.

Recomendacao:

```text
1. Configurar DNS do roteador/DHCP para 1.1.1.1 e 8.8.8.8; ou
2. Migrar para dominio proprio gerenciado por Cloudflare; e
3. Usar endpoint estavel para agentes, como agent.<dominio>.
```

### Basic Auth e MVP

HTTP Basic Auth e suficiente para MVP, mas nao substitui login real.

Evolucao:

```text
Usuarios, sessoes, RBAC, auditoria e politicas de senha.
```

### VM unica

PostgreSQL, backend, frontend e Nginx rodam no mesmo Edge Node.

Risco:

```text
Sem alta disponibilidade.
```

Mitigacao:

```text
Backups frequentes, restore testado e monitoramento de disco/memoria.
```

## Proximos passos recomendados

1. Criar pacote `.zip` versionado contendo apenas `agent-windows`.
2. Configurar DNS central da rede ou dominio proprio em Cloudflare.
3. Criar script de instalacao assistida do agente com prompts seguros.
4. Adicionar endpoint de health especifico do frontend, se necessario.
5. Automatizar criacao de `.env.production` sem registrar secrets.
6. Configurar backup periodico do PostgreSQL.
7. Testar restore em ambiente separado.
8. Adicionar monitoramento de certificado, disco, memoria, swap e containers unhealthy.
