# Postmortems operacionais

Este documento registra incidentes, falhas, degradacoes e aprendizados encontrados durante o desenvolvimento e a implantacao do IT Center Security Cloud.

O objetivo nao e atribuir culpa. O objetivo e documentar sintomas, impacto, causa raiz, correcao, validacao e melhorias futuras para que a operacao fique mais confiavel a cada ciclo.

## Contexto

O projeto foi implantado em uma VM Oracle Cloud com Ubuntu Server 24.04 LTS, Docker, Docker Compose, PostgreSQL, FastAPI, Next.js e Nginx.

Ambiente principal:

```text
Cloud: Oracle Cloud
Sistema operacional: Ubuntu Server 24.04 LTS
Dominio: itcenter-daniel.chickenkiller.com
IP publico: 147.15.78.220
Rede Docker: itcenter-network
Aplicacao: /opt/itcenter/app/it-center-security-cloud
Backups: /opt/itcenter/backups
```

## Padrao de severidade

```text
Informativa - evento sem impacto, mas com valor de aprendizado
Baixa       - problema localizado, sem indisponibilidade relevante
Media       - funcionalidade degradada ou bloqueio temporario
Alta        - servico principal indisponivel ou deploy bloqueado
Critica     - perda de dados, exposicao de seguranca ou indisponibilidade ampla
```

## Padrao dos incidentes

Cada incidente segue o formato:

```text
Resumo
Severidade
Data
Ambiente
Sintomas
Impacto
Linha do tempo
Causa raiz
Correcao aplicada
Como validar
Licoes aprendidas
Melhorias futuras
Automacao recomendada
```

---

# INCIDENTE 001

## Resumo

Docker Engine ainda nao estava instalado na VM de producao.

## Severidade

```text
Alta
```

## Data

```text
2026-06-26
```

## Ambiente

```text
Producao
Oracle Cloud
Ubuntu 24.04 LTS
Docker
```

## Sintomas

Comandos Docker nao estavam disponiveis no host.

## Impacto

* Stack de producao nao podia ser criada.
* Containers de PostgreSQL, backend, frontend e Nginx nao podiam iniciar.
* Deploy bloqueado.

## Linha do tempo

```text
T+00 - Preparacao da VM iniciada
T+05 - Validacao de Docker solicitada
T+06 - Docker ausente identificado
T+10 - Docker Engine instalado
T+12 - docker --version validado
```

## Causa raiz

A VM Oracle foi provisionada como Ubuntu limpo, sem Docker instalado por padrao.

## Correcao aplicada

Instalacao do Docker Engine.

## Como validar

```bash
docker --version
docker ps
```

## Licoes aprendidas

* Docker precisa ser validado antes de qualquer etapa de Compose.
* A instalacao do runtime deve fazer parte do bootstrap versionado.

## Melhorias futuras

* Automatizar instalacao do Docker no bootstrap.
* Validar versao minima do Docker no preflight.

## Automacao recomendada

```bash
command -v docker >/dev/null 2>&1 || exit 1
docker version >/dev/null 2>&1 || exit 1
```

---

# INCIDENTE 002

## Resumo

Docker Compose ainda nao estava instalado ou validado na VM.

## Severidade

```text
Alta
```

## Data

```text
2026-06-26
```

## Ambiente

```text
Producao
Oracle Cloud
Docker Compose
```

## Sintomas

O deploy via `docker compose` nao poderia ser executado sem o plugin Compose.

## Impacto

* Stack nao poderia ser orquestrada.
* `docker-compose.production.yml` nao poderia ser validado.
* Deploy bloqueado.

## Linha do tempo

```text
T+00 - Docker instalado
T+03 - Validacao do Compose iniciada
T+04 - Necessidade do Docker Compose confirmada
T+08 - Docker Compose instalado
T+10 - docker compose version validado
```

## Causa raiz

Docker Engine e Docker Compose sao componentes diferentes. Instalar Docker nao garante que o plugin Compose esteja disponivel.

## Correcao aplicada

Instalacao do Docker Compose Plugin.

## Como validar

```bash
docker compose version
docker compose --help
```

## Licoes aprendidas

* Docker Compose v2 deve ser dependencia explicita da plataforma.
* Preflight precisa validar Docker e Compose separadamente.

## Melhorias futuras

* Bootstrap deve instalar Compose junto com Docker.
* Documentar versao minima suportada.

## Automacao recomendada

```bash
docker compose version >/dev/null 2>&1 || exit 1
```

---

# INCIDENTE 003

## Resumo

Usuario `ubuntu` precisava de permissao para executar Docker.

## Severidade

```text
Media
```

## Data

```text
2026-06-26
```

## Ambiente

```text
Producao
Oracle Cloud
Linux
Docker
```

## Sintomas

Usuario operacional poderia receber erro de permissao ao executar comandos Docker.

## Impacto

* Operacao ficaria dependente de `sudo`.
* Scripts de deploy poderiam falhar se assumissem acesso ao Docker.

## Linha do tempo

```text
T+00 - Docker instalado
T+03 - Permissao operacional revisada
T+05 - Usuario ubuntu adicionado ao grupo docker
T+10 - Nova sessao SSH recomendada
```

## Causa raiz

O socket Docker exige permissao especifica. Usuarios comuns nao acessam Docker automaticamente.

## Correcao aplicada

```bash
sudo usermod -aG docker ubuntu
```

## Como validar

```bash
groups
docker ps
```

## Licoes aprendidas

* Alteracao de grupo exige nova sessao.
* Scripts devem falhar claramente se Docker nao estiver acessivel.

## Melhorias futuras

* Bootstrap deve configurar grupo Docker.
* Preflight deve validar acesso ao Docker daemon.

## Automacao recomendada

```bash
docker ps >/dev/null 2>&1 || exit 1
```

---

# INCIDENTE 004

## Resumo

Clone do repositorio privado dependia de autenticacao SSH configurada no GitHub.

## Severidade

```text
Media
```

## Data

```text
2026-06-26
```

## Ambiente

```text
Producao
Oracle Cloud
GitHub
SSH
```

## Sintomas

Clone privado nao funcionaria sem chave SSH autorizada.

## Impacto

* Codigo da aplicacao nao poderia ser baixado na VM.
* Deploy bloqueado antes da etapa de build.

## Linha do tempo

```text
T+00 - Necessidade de clone privado identificada
T+05 - Chave SSH configurada na VM
T+10 - Chave cadastrada no GitHub
T+12 - Clone via SSH validado
```

## Causa raiz

Repositorios privados exigem autenticacao. A VM inicialmente nao tinha chave autorizada no GitHub.

## Correcao aplicada

Configurar chave SSH da VM e clonar usando:

```bash
git clone git@github.com:DanielAzeved0/it-center-security-cloud.git
```

## Como validar

```bash
ssh -T git@github.com
git clone git@github.com:DanielAzeved0/it-center-security-cloud.git
```

## Licoes aprendidas

* Acesso ao codigo e pre-requisito do deploy.
* SSH evita uso de tokens no servidor.

## Melhorias futuras

* Documentar processo de criacao e rotacao de chave SSH.
* Usar chave com escopo minimo quando possivel.

## Automacao recomendada

```bash
ssh -T git@github.com
```

---

# INCIDENTE 005

## Resumo

Arquivo `.env.production` precisava ser criado e preenchido com secrets reais.

## Severidade

```text
Alta
```

## Data

```text
2026-06-26
```

## Ambiente

```text
Producao
Docker Compose
Secrets
```

## Sintomas

Compose e aplicacao dependem de variaveis de ambiente reais.

## Impacto

* Banco nao inicializa corretamente sem credenciais.
* Backend nao conecta ao banco sem `DATABASE_URL`.
* Agente nao autentica sem `AGENT_API_KEY`.

## Linha do tempo

```text
T+00 - Template .env.production.example identificado
T+03 - .env.production criado
T+05 - POSTGRES_PASSWORD gerado
T+06 - AGENT_API_KEY gerado
T+10 - Variaveis revisadas
```

## Causa raiz

Templates nao sao configuracoes de producao. Placeholders precisam ser substituidos.

## Correcao aplicada

```bash
cp .env.production.example .env.production
openssl rand -hex 32
```

## Como validar

```bash
grep -E 'DOMAIN_NAME|POSTGRES_PASSWORD|DATABASE_URL|AGENT_API_KEY' .env.production
sh infra/scripts/preflight-production.sh
```

## Licoes aprendidas

* Secrets devem ser gerados com entropia suficiente.
* Preflight deve bloquear placeholders.

## Melhorias futuras

* Criar script seguro para gerar `.env.production`.
* Adicionar validacao de consistencia entre `POSTGRES_PASSWORD` e `DATABASE_URL`.

## Automacao recomendada

```bash
grep -q 'REPLACE_WITH\|monitor.example.com' .env.production && exit 1
```

---

# INCIDENTE 006

## Resumo

Placeholders em arquivos de ambiente poderiam chegar ao deploy.

## Severidade

```text
Alta
```

## Data

```text
2026-06-26
```

## Ambiente

```text
Producao
Preflight
Docker Compose
```

## Sintomas

Valores como `monitor.example.com` ou `REPLACE_WITH...` poderiam estar presentes em `.env.production`.

## Impacto

* Certificados TLS apontariam para dominio incorreto.
* Banco poderia usar senha insegura.
* Agente poderia usar chave insegura.
* Deploy poderia subir com configuracao invalida.

## Linha do tempo

```text
T+00 - .env.production criado a partir do template
T+05 - Risco de placeholder identificado
T+08 - Validacao adicionada ao preflight
T+10 - Deploy protegido contra placeholders
```

## Causa raiz

Arquivos example usam valores ficticios por design.

## Correcao aplicada

Validacao no preflight para bloquear placeholders.

## Como validar

```bash
sh infra/scripts/preflight-production.sh
```

## Licoes aprendidas

* Templates devem ser tratados como entrada insegura.
* O deploy nao deve depender de revisao manual de secrets.

## Melhorias futuras

* Gerar `.env.production` por wizard seguro.
* Validar formato de dominio e URL do banco.

## Automacao recomendada

```bash
case "$DOMAIN_NAME" in
  monitor.example.com|example.com|localhost) exit 1 ;;
esac
```

---

# INCIDENTE 007

## Resumo

Compose de producao precisava ser validado antes do build e do up.

## Severidade

```text
Media
```

## Data

```text
2026-06-26
```

## Ambiente

```text
Producao
Docker Compose
```

## Sintomas

Qualquer erro no arquivo `infra/docker-compose.production.yml` bloquearia a subida da stack.

## Impacto

* Deploy poderia falhar no meio do processo.
* Diagnostico ficaria mais lento.

## Linha do tempo

```text
T+00 - Compose de producao revisado
T+03 - docker compose config executado
T+05 - Configuracao validada
```

## Causa raiz

Compose e sensivel a paths, env files, volumes e sintaxe.

## Correcao aplicada

Validacao obrigatoria:

```bash
docker compose --env-file .env.production -f infra/docker-compose.production.yml config
```

## Como validar

```bash
docker compose --env-file .env.production -f infra/docker-compose.production.yml config -q
```

## Licoes aprendidas

* Validar Compose antes do build reduz falha tardia.

## Melhorias futuras

* Executar `docker compose config -q` em CI.

## Automacao recomendada

```bash
docker compose --env-file .env.production -f infra/docker-compose.production.yml config -q || exit 1
```

---

# INCIDENTE 008

## Resumo

Pouca memoria na VM da Oracle exigiu criacao de Swap.

## Severidade

```text
Media
```

## Data

```text
2026-06-26
```

## Ambiente

```text
Producao
Oracle Cloud
Docker
```

## Sintomas

Risco de instabilidade durante build e execucao dos containers.

## Impacto

* Builds poderiam falhar.
* Containers poderiam reiniciar.
* Deploy poderia ficar instavel.

## Linha do tempo

```text
T+00 - Build e containers avaliados
T+05 - Limite de memoria percebido
T+10 - Swap criada
T+15 - Ambiente estabilizado
```

## Causa raiz

VM gratuita possui recursos limitados.

## Correcao aplicada

Criacao de Swap na VM.

## Como validar

```bash
free -h
docker stats
```

## Licoes aprendidas

* Swap ajuda em MVP com VM pequena.
* Swap nao substitui dimensionamento correto para producao critica.

## Melhorias futuras

* Monitorar uso de memoria.
* Avaliar instancia maior se houver uso real.

## Automacao recomendada

```bash
awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo
```

---

# INCIDENTE 009

## Resumo

Healthcheck do frontend ficou unhealthy por usar alvo inadequado ao runtime do Next.js.

## Severidade

```text
Media
```

## Data

```text
2026-06-26
```

## Ambiente

```text
Producao
Docker
Next.js
Healthcheck
```

## Sintomas

Container frontend aparecia como unhealthy.

## Impacto

* Nginx poderia aguardar frontend healthy.
* Deploy poderia ser considerado falho mesmo com app funcional.

## Linha do tempo

```text
T+00 - Deploy iniciado
T+05 - Frontend iniciou
T+06 - Frontend unhealthy
T+08 - Healthcheck analisado
T+15 - Causa raiz identificada
T+18 - Healthcheck corrigido
T+20 - Frontend healthy
```

## Causa raiz

Healthcheck nao estava alinhado ao hostname/rota que respondia corretamente dentro do container.

## Correcao aplicada

Ajuste do healthcheck para usar o alvo interno correto.

## Como validar

```bash
docker compose --env-file .env.production -f infra/docker-compose.production.yml ps
docker compose --env-file .env.production -f infra/docker-compose.production.yml exec -T nginx wget -q -O - http://frontend:3000/
```

## Licoes aprendidas

* Healthcheck precisa ser testado dentro do container.
* `localhost`, `127.0.0.1` e hostnames internos podem se comportar de forma diferente conforme runtime.

## Melhorias futuras

* Padronizar healthchecks por servico.
* Documentar endpoint de health do frontend.

## Automacao recomendada

```bash
docker inspect --format '{{.State.Health.Status}}' itcenter-frontend
```

---

# INCIDENTE 010

## Resumo

Healthcheck do backend precisava confirmar a disponibilidade real da API.

## Severidade

```text
Baixa
```

## Data

```text
2026-06-26
```

## Ambiente

```text
Producao
Docker
FastAPI
Healthcheck
```

## Sintomas

Necessidade de validar `/api/v1/health` dentro do container.

## Impacto

Sem healthcheck confiavel, Compose poderia considerar backend pronto antes da API responder.

## Linha do tempo

```text
T+00 - Backend iniciado
T+03 - Healthcheck executado
T+05 - API respondeu /api/v1/health
```

## Causa raiz

Servicos web precisam de validacao HTTP, nao apenas processo iniciado.

## Correcao aplicada

Healthcheck baseado em chamada HTTP para `/api/v1/health`.

## Como validar

```bash
docker exec -it itcenter-backend wget -q -O - http://127.0.0.1:8000/api/v1/health
```

## Licoes aprendidas

* Processo ativo nao significa API pronta.

## Melhorias futuras

* Criar readiness check que valide banco quando necessario.

## Automacao recomendada

```bash
wget -q -O /dev/null http://127.0.0.1:8000/api/v1/health
```

---

# INCIDENTE 011

## Resumo

Nginx dependia de certificados TLS e secrets corretamente montados.

## Severidade

```text
Alta
```

## Data

```text
2026-06-26
```

## Ambiente

```text
Producao
Nginx
TLS
Docker
```

## Sintomas

Nginx poderia falhar se certificados ou `dashboard.htpasswd` estivessem ausentes ou inacessiveis.

## Impacto

* HTTPS indisponivel.
* Dashboard inacessivel.
* Reverse proxy indisponivel.

## Linha do tempo

```text
T+00 - Nginx configurado
T+05 - Certificados validados
T+08 - Basic Auth validado
T+10 - Nginx healthy
```

## Causa raiz

Nginx depende de arquivos externos montados via bind mount.

## Correcao aplicada

Validar certificados, secrets e permissao antes do deploy final.

## Como validar

```bash
docker exec -it itcenter-nginx nginx -t
docker logs itcenter-nginx
ls -l /etc/letsencrypt/live/itcenter-daniel.chickenkiller.com/
ls -la .secrets
```

## Licoes aprendidas

* Reverse proxy e ponto critico de producao.
* Secrets e certificados devem estar no preflight.

## Melhorias futuras

* Automatizar teste de `nginx -t`.
* Monitorar expiracao de certificado.

## Automacao recomendada

```bash
test -f /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem || exit 1
test -f .secrets/dashboard.htpasswd || exit 1
```

---

# INCIDENTE 012

## Resumo

Arquivo `dashboard.htpasswd` apresentou `Permission denied`.

## Severidade

```text
Alta
```

## Data

```text
2026-06-26
```

## Ambiente

```text
Producao
Nginx
Basic Auth
Docker
```

## Sintomas

Dashboard nao autenticava corretamente e Nginx registrava erro de permissao.

## Impacto

* Dashboard inacessivel.
* Basic Auth indisponivel.

## Linha do tempo

```text
T+00 - Dashboard protegido com Basic Auth
T+05 - Erro Permission denied identificado
T+08 - Permissoes revisadas
T+10 - chmod aplicado
T+12 - Dashboard autenticando
```

## Causa raiz

Permissoes inadequadas em `.secrets` ou `dashboard.htpasswd`.

## Correcao aplicada

```bash
chmod 700 .secrets
chmod 644 .secrets/dashboard.htpasswd
```

## Como validar

```bash
ls -la .secrets
docker logs itcenter-nginx
curl --user admin:SENHA_FORTE_AQUI https://itcenter-daniel.chickenkiller.com
```

## Licoes aprendidas

* Problemas de autenticacao podem ser problemas de permissao.

## Melhorias futuras

* Preflight deve validar existencia e permissao minima do arquivo.

## Automacao recomendada

```bash
test -r .secrets/dashboard.htpasswd || exit 1
```

---

# INCIDENTE 013

## Resumo

Let's Encrypt dependia de DNS correto e porta 80 aberta.

## Severidade

```text
Alta
```

## Data

```text
2026-06-26
```

## Ambiente

```text
Producao
Let's Encrypt
Oracle Cloud
DNS
```

## Sintomas

Certificado nao poderia ser emitido se o dominio nao resolvesse ou se a porta 80 estivesse bloqueada.

## Impacto

* HTTPS nao ficaria disponivel.
* Nginx com TLS nao iniciaria corretamente.

## Linha do tempo

```text
T+00 - Dominio criado
T+05 - Porta 80 revisada
T+10 - Certbot executado
T+15 - Certificado emitido
```

## Causa raiz

Validacao ACME HTTP exige acesso publico ao dominio pela porta 80.

## Correcao aplicada

Abrir porta 80 e validar DNS antes da emissao.

## Como validar

```bash
dig itcenter-daniel.chickenkiller.com
curl -I http://itcenter-daniel.chickenkiller.com
ls -l /etc/letsencrypt/live/itcenter-daniel.chickenkiller.com/
```

## Licoes aprendidas

* TLS depende de rede, DNS e firewall.

## Melhorias futuras

* Criar checklist especifico de ACME antes de emitir certificados.

## Automacao recomendada

```bash
test -f /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem || exit 1
```

---

# INCIDENTE 014

## Resumo

DNS da Vivo retornava NXDOMAIN enquanto resolvedores publicos ja resolviam corretamente.

## Severidade

```text
Baixa
```

## Data

```text
2026-06-26
```

## Ambiente

```text
Producao
DNS
Rede externa
```

## Sintomas

Dominio nao resolvia em determinado provedor local.

## Impacto

* Alguns usuarios poderiam nao acessar o dominio temporariamente.
* Risco de diagnostico incorreto como falha da aplicacao.

## Linha do tempo

```text
T+00 - Dominio configurado
T+05 - Falha observada no DNS da Vivo
T+08 - Google DNS testado
T+10 - Cloudflare testado
T+12 - Quad9 testado
T+15 - Causa classificada como propagacao/cache do provedor
```

## Causa raiz

Propagacao DNS parcial ou cache do resolvedor da Vivo.

## Correcao aplicada

Testes com resolvedores publicos:

```bash
dig @8.8.8.8 itcenter-daniel.chickenkiller.com
dig @1.1.1.1 itcenter-daniel.chickenkiller.com
dig @9.9.9.9 itcenter-daniel.chickenkiller.com
```

## Como validar

Comparar resposta de multiplos resolvedores.

## Licoes aprendidas

* DNS deve ser validado por mais de um resolvedor.
* Falha em provedor local nao significa falha de infraestrutura.

## Melhorias futuras

* Documentar procedimento padrao de validacao DNS.

## Automacao recomendada

```bash
for dns in 8.8.8.8 1.1.1.1 9.9.9.9; do
  dig @"$dns" "$DOMAIN_NAME"
done
```

---

# INCIDENTE 015

## Resumo

Comunicacao entre containers precisou ser validada pela rede Docker.

## Severidade

```text
Media
```

## Data

```text
2026-06-26
```

## Ambiente

```text
Producao
Docker Network
itcenter-network
```

## Sintomas

Era necessario confirmar que frontend, backend, Nginx e PostgreSQL se comunicavam internamente.

## Impacto

* Dashboard poderia nao consultar API.
* Backend poderia nao acessar banco.
* Nginx poderia nao acessar upstreams.

## Linha do tempo

```text
T+00 - Containers iniciados
T+05 - Healthchecks executados
T+08 - Testes internos iniciados
T+12 - Comunicacao validada
```

## Causa raiz

Ambientes Docker dependem de rede, DNS interno e nomes de servico corretos.

## Correcao aplicada

Execucao de testes internos por container.

## Como validar

```bash
docker network inspect itcenter-network
docker exec -it itcenter-backend wget -q -O - http://127.0.0.1:8000/api/v1/health
docker compose --env-file .env.production -f infra/docker-compose.production.yml exec -T nginx wget -q -O - http://frontend:3000/
docker exec -it itcenter-nginx wget -q -O - http://127.0.0.1/healthz
```

## Licoes aprendidas

* Testes internos reduzem ruído causado por DNS publico, firewall e navegador.

## Melhorias futuras

* Smoke tests devem validar comunicacao entre servicos.

## Automacao recomendada

Adicionar smoke tests ao `deploy.sh`.

---

# INCIDENTE 016

## Resumo

Containers passaram de unhealthy para healthy apos ajustes de healthcheck, memoria e permissao.

## Severidade

```text
Informativa
```

## Data

```text
2026-06-26
```

## Ambiente

```text
Producao
Docker Compose
```

## Sintomas

Durante a implantacao alguns servicos exigiram ajustes antes de ficarem healthy.

## Impacto

* Deploy nao deveria ser considerado completo ate todos os containers ficarem healthy.

## Linha do tempo

```text
T+00 - Containers iniciados
T+05 - Estados avaliados
T+10 - Ajustes aplicados
T+20 - Todos os containers healthy
```

## Causa raiz

Combinacao de ajustes operacionais: healthcheck, memoria, TLS e secrets.

## Correcao aplicada

* Healthcheck ajustado.
* Permissao de Basic Auth corrigida.
* Swap criada.
* TLS validado.

## Como validar

```bash
docker ps
docker compose --env-file .env.production -f infra/docker-compose.production.yml ps
```

## Licoes aprendidas

* `healthy` deve ser criterio obrigatorio de conclusao do deploy.

## Melhorias futuras

* Deploy deve aguardar healthchecks automaticamente.

## Automacao recomendada

```bash
docker inspect --format '{{.State.Health.Status}}' itcenter-nginx
```

---

# INCIDENTE 017

## Resumo

Dashboard ficou vazio apos deploy.

## Severidade

```text
Informativa
```

## Data

```text
2026-06-26
```

## Ambiente

```text
Producao
Dashboard
Windows Agent
```

## Sintomas

Dashboard carregava, mas sem maquinas listadas.

## Impacto

* Visualmente poderia parecer ausencia de dados.
* Nao havia impacto na infraestrutura.

## Linha do tempo

```text
T+00 - Dashboard acessado
T+02 - Lista vazia observada
T+05 - Estado do agente revisado
T+08 - Confirmado que nenhum agente havia enviado check-in
```

## Causa raiz

Windows Agent ainda nao estava integrado ao ambiente publicado.

## Correcao aplicada

Nenhuma correcao necessaria.

## Como validar

```bash
curl --user admin:SENHA_FORTE_AQUI https://itcenter-daniel.chickenkiller.com
```

## Licoes aprendidas

* Dashboard vazio pode ser estado esperado antes da integracao dos agentes.

## Melhorias futuras

* Criar empty state explicito no dashboard.
* Evoluir Windows Agent como produto independente.

## Automacao recomendada

Criar smoke test futuro simulando check-in de agente em ambiente controlado.

---

# INCIDENTE 018

## Resumo

Perda da chave SSH pessoal de acesso ao Edge Node e exposicao acidental de uma chave privada durante a recuperacao.

## Severidade

```text
Alta
```

## Data

```text
2026-07-28
```

## Ambiente

```text
Producao
Oracle Cloud
SSH
GitHub Actions
```

## Sintomas

Nenhuma chave SSH pessoal disponivel para acessar `itcenter-edge-01`.

## Impacto

* Acesso administrativo a VM bloqueado.
* Sem esse acesso nao era possivel operar backup/restore/rollback/TLS nem redefinir credenciais do dashboard.

## Linha do tempo

```text
T+00 - Chave SSH pessoal ausente identificada
T+05 - Workflow temporario ssh-access-recovery.yml criado, reaproveitando o
       secret PROD_SSH_PRIVATE_KEY ja usado pelo deploy
T+10 - Novo par de chaves gerado localmente
T+12 - Conteudo da chave privada colado por engano no canal de suporte
T+15 - Chave publica correspondente ainda assim adicionada ao
       authorized_keys via workflow, unica opcao disponivel no momento
T+18 - Novo par de chaves gerado corretamente
T+20 - Chave comprometida removida do authorized_keys da VM, chave nova
       validada com sucesso
T+22 - Workflow temporario removido do repositorio
```

## Causa raiz

Chave SSH pessoal perdida sem copia de backup. Nao havia um segundo fator de acesso administrativo a VM alem da chave SSH individual.

## Correcao aplicada

* Workflow `ssh-access-recovery.yml` criado, executado uma unica vez via `workflow_dispatch` reaproveitando o secret `PROD_SSH_PRIVATE_KEY` ja usado pelo deploy, e removido do repositorio logo em seguida.
* Chave privada exposta foi tratada como comprometida: sua chave publica foi removida do `authorized_keys` assim que uma chave nova ficou disponivel.

## Como validar

```bash
cat ~/.ssh/authorized_keys
```

Confirmar que restam apenas chaves conhecidas (`itcenter-edge-01`, `github-actions-itcenter` e a chave pessoal vigente).

## Licoes aprendidas

* Nunca colar material de chave privada em nenhum canal de texto. Se acontecer, tratar a chave como comprometida e revoga-la imediatamente, mesmo que pareca inofensivo.
* Um workflow que injeta chaves SSH usando um secret ja existente e uma forma valida de recuperacao de ultimo recurso, mas deve ser removido do repositorio assim que usado, pois representa um vetor de escalada enquanto existir.
* Depender de uma unica chave SSH pessoal sem backup e um ponto unico de falha para o acesso administrativo.

## Melhorias futuras

* Guardar uma copia de recuperacao da chave SSH pessoal em um cofre de senhas.
* Documentar acesso alternativo via OCI Console/Serial Console como plano B, evitando depender apenas do GitHub Actions em uma proxima perda de chave.

## Automacao recomendada

```bash
grep -c '^ssh-' ~/.ssh/authorized_keys
```

---

# INCIDENTE 019

## Resumo

Nenhum usuario administrativo existia na tabela `users` em producao, apesar da EPIC 12 constar como concluida.

## Severidade

```text
Alta
```

## Data

```text
2026-07-28
```

## Ambiente

```text
Producao
PostgreSQL
Backend
```

## Sintomas

A tela de login administrativo (`/login`) respondia `{"detail":"Invalid credentials"}` para qualquer tentativa.

## Impacto

* Acesso administrativo ao dashboard totalmente indisponivel.
* Nenhuma auditoria ou operacao via RBAC era possivel ate a criacao de um usuario.

## Linha do tempo

```text
T+00 - Tentativa de login administrativo falhando repetidamente
T+05 - Consulta direta SELECT id, email, name, role, status FROM users
       retornou 0 linhas
T+08 - Identificado que backend/create_admin.py nunca havia sido
       executado no ambiente de producao
T+10 - create_admin.py copiado manualmente para dentro do container,
       ja que nao faz parte da imagem Docker do backend
T+12 - Primeiro admin criado, porem com senha fraca por erro de
       digitacao em variavel de shell (variavel errada referenciada)
T+15 - Senha corrigida via atualizacao direta de password_hash usando
       o mesmo hash_password() do backend
```

## Causa raiz

A implementacao do login (EPIC 12, ADR-021, ADR-022) foi validada em ambiente de teste, mas a etapa de seed do primeiro usuario administrativo (`backend/create_admin.py`) nunca foi executada no ambiente de producao real. Esse script tambem nao faz parte da imagem Docker do backend, que copia apenas `app/`, `migrations/` e `apply_migrations.py`.

## Correcao aplicada

* `create_admin.py` copiado manualmente para o container (`docker cp`) e executado com `ADMIN_EMAIL`/`ADMIN_NAME`/`ADMIN_PASSWORD` para criar o primeiro admin.
* Senha redefinida em seguida via atualizacao direta do `password_hash` (PBKDF2), reaproveitando `hash_password()` do proprio backend para manter compatibilidade com `verify_password()`.

## Como validar

```bash
docker exec -i itcenter-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT count(*) FROM users WHERE role='admin' AND status='active';"
```

## Licoes aprendidas

* "Deploy concluido" nao significa "seed de dados concluido". O checklist de deploy precisa incluir a criacao do primeiro admin como etapa explicita, nao implicita.
* Scripts de setup unico como `create_admin.py`, quando ficam fora da imagem e fora do fluxo de deploy, sao facilmente esquecidos justamente porque so importam uma vez.

## Melhorias futuras

* Incluir `create_admin.py` na imagem do backend ou chama-lo a partir de `deploy.sh` de forma idempotente (ele ja retorna sem sobrescrever se o e-mail existir).
* Adicionar ao preflight ou aos smoke tests uma checagem de que existe ao menos um usuario `admin` ativo apos o deploy.

## Automacao recomendada

```bash
docker exec -i itcenter-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc \
  "SELECT count(*) FROM users WHERE role='admin' AND status='active';" | grep -qv '^0$' || exit 1
```

---

# INCIDENTE 020

## Resumo

Loop de login no dashboard: o Basic Auth do Nginx colidia com o Bearer token emitido pelo login da aplicacao.

## Severidade

```text
Alta
```

## Data

```text
2026-07-28
```

## Ambiente

```text
Producao
Nginx
Dashboard
Backend
```

## Sintomas

Apos preencher corretamente o Basic Auth e o login administrativo, o navegador voltava repetidamente ao prompt de Basic Auth. Chamadas para `/me`, `/machines`, `/alerts` e `/security-events` retornavam `401`.

## Impacto

* Dashboard inutilizavel mesmo com credenciais corretas nas duas camadas de autenticacao.

## Linha do tempo

```text
T+00 - Login administrativo validado via curl, funcionando fora do navegador
T+05 - Reproduzido no navegador: loop entre Basic Auth e tela de login
T+10 - Network tab mostrou 401 em /api/backend/api/v1/auth/login e,
       apos login, em /me, /machines, /alerts e /security-events
T+15 - Identificado que essas chamadas enviam Authorization: Bearer
       <token>, substituindo o Authorization: Basic que o Nginx espera
       em location /
T+18 - Nova location ^~ /api/backend/ criada no Nginx, isentando essas
       rotas do Basic Auth, ja protegidas por RBAC/token da aplicacao
T+20 - Alteracao commitada (c95586c), enviada ao repositorio e aplicada
       na VM via git pull + docker compose restart nginx
T+22 - Login validado com sucesso no navegador
```

## Causa raiz

O HTTP permite apenas um cabecalho `Authorization` por requisicao. A configuracao original do Nginx aplicava `auth_basic` em `location /` sem excecao, entao qualquer chamada do dashboard que definisse `Authorization: Bearer ...` para o token da aplicacao perdia, do ponto de vista do Nginx, a credencial Basic Auth que ele exigia.

## Correcao aplicada

Adicionada uma `location ^~ /api/backend/` sem `auth_basic` no Nginx, mantendo o proxy para o frontend como antes. Essas rotas continuam protegidas pelo RBAC/Bearer da propria aplicacao, seguindo o mesmo padrao ja usado para `POST /api/v1/agent/checkin`. Decisao registrada em ADR-023.

## Como validar

```bash
curl -s -u admin:SENHA -X POST https://itcenter-daniel.chickenkiller.com/api/backend/api/v1/auth/login -H "Content-Type: application/json" -d @login.json
```

Confirmar tambem que o dashboard permanece logado ao navegar entre paginas apos o login.

## Licoes aprendidas

* Basic Auth aplicado indiscriminadamente sobre toda a aplicacao conflita com qualquer esquema de autenticacao propria que tambem use o cabecalho `Authorization`.
* Um "loop de login" deve ser investigado olhando os headers de resposta (presenca ou ausencia de `www-authenticate`) antes de suspeitar de senha errada ou cache do navegador.

## Melhorias futuras

* Reavaliar se o Basic Auth do MVP ainda se justifica agora que existe login administrativo completo (ADR-021, ADR-022), ou se pode ser removido em uma fase futura.

## Automacao recomendada

```bash
curl -s -o /dev/null -w '%{http_code}' -u admin:SENHA https://itcenter-daniel.chickenkiller.com/api/backend/api/v1/health
```

---

# INCIDENTE 021

## Resumo

Renovacao de TLS bloqueada porque a imagem `certbot/certbot:v4.21.0` referenciada no Compose de producao nunca existiu no Docker Hub.

## Severidade

```text
Media
```

## Data

```text
2026-07-28
```

## Ambiente

```text
Producao
Docker
Certbot
```

## Sintomas

```text
docker: Error response from daemon: failed to resolve reference
"docker.io/certbot/certbot:v4.21.0": docker.io/certbot/certbot:v4.21.0: not found
```

ao executar `TLS_RENEW_DRY_RUN=1 sh infra/scripts/renew-tls.sh`.

## Impacto

* Validacao de renovacao de TLS (item pendente da EPIC 13) bloqueada.
* Uma renovacao real de certificado, se necessaria, tambem falharia com o mesmo erro.

## Linha do tempo

```text
T+00 - TLS_RENEW_DRY_RUN=1 sh infra/scripts/renew-tls.sh executado
T+01 - Erro "not found" ao puxar certbot/certbot:v4.21.0
T+03 - Consulta direta a API do Docker Hub confirmou 404 para essa tag
T+05 - Confirmado via GitHub Releases que a versao mais recente do
       Certbot e v5.7.0, tag existente e valida no Docker Hub (200)
T+07 - infra/docker-compose.production.yml atualizado para
       certbot/certbot:v5.7.0
```

## Causa raiz

O Compose de producao referenciava uma tag de imagem (`v4.21.0`) que nunca existiu no Docker Hub para `certbot/certbot`. Como o servico `certbot` roda apenas sob o profile `maintenance`, essa referencia invalida nao aparecia em nenhum smoke test ou deploy de rotina, e so foi descoberta ao validar a renovacao de TLS de fato.

## Correcao aplicada

Atualizada a imagem para `certbot/certbot:v5.7.0` (tag existente, confirmada via API do Docker Hub e via GitHub Releases do Certbot).

## Como validar

```bash
docker compose --env-file .env.production -f infra/docker-compose.production.yml --profile maintenance pull certbot
TLS_RENEW_DRY_RUN=1 sh infra/scripts/renew-tls.sh
```

## Licoes aprendidas

* Imagens usadas apenas por profiles opcionais (`maintenance`) nao sao validadas pelos smoke tests de deploy nem pelo Docker Scout de rotina, entao uma tag invalida pode passar despercebida por muito tempo.
* Tags de imagens externas devem ser confirmadas por uma fonte real (API do registry ou releases oficiais) antes de fixar a versao, nao apenas assumidas.

## Melhorias futuras

* Incluir `docker compose --profile maintenance pull` no preflight ou em uma checagem periodica, mesmo que o servico nao suba por padrao.
* Revisar periodicamente se ha versao mais recente do Certbot compativel.

## Automacao recomendada

```bash
docker compose --env-file .env.production -f infra/docker-compose.production.yml --profile maintenance config -q
```

---

# INCIDENTE 022

## Resumo

O unico usuario administrador da tenancy Oracle Cloud perdeu o segundo fator de autenticacao (MFA), sem fator de backup nem segundo administrador cadastrado, bloqueando qualquer acesso ao Console OCI ou via `oci` CLI.

## Severidade

```text
Alta
```

## Data

```text
2026-08-15
```

## Ambiente

```text
Producao
Oracle Cloud
Console OCI / IAM
Terraform (EPIC 15)
```

## Sintomas

Tentativa de login no Console Oracle Cloud, para retomar a EPIC 15 (criar o bucket de Object Storage do state remoto do Terraform), bloqueada na etapa de MFA: o segundo fator estava vinculado a um celular antigo, sem fator de backup configurado.

## Impacto

* Nenhuma acao no Console ou via `oci` CLI e possivel ate a conta ser recuperada: criar/rotacionar API keys, criar o bucket de Object Storage para o state remoto, ou qualquer recriacao de emergencia da VM ou da rede (cenario de disaster recovery da EPIC 15/`docs/architecture/IAC.md`).
* A aplicacao em si (dashboard, backend, agente, Nginx) continua funcionando normalmente em `itcenter-edge-01` — o bloqueio e apenas para operacoes administrativas de infraestrutura na nuvem.
* Combinado com a dependencia de uma unica chave SSH pessoal (INCIDENTE 018), a operacao do projeto passa a depender inteiramente do acesso SSH continuo a VM, sem plano B caso a VM ou a rede precisem ser recriadas do zero.
* Migracao do state do Terraform para backend remoto (ultimo item pendente da EPIC 15) bloqueada sem previsao.

## Linha do tempo

```text
T+00 - Tentativa de acessar o Console Oracle Cloud para criar o bucket
       de Object Storage do state remoto (EPIC 15)
T+05 - Login bloqueado na etapa de MFA: segundo fator vinculado a um
       celular antigo, sem fator de backup configurado
T+10 - Confirmado que nao existe segundo usuario administrador
       cadastrado na tenancy
T+15 - Investigacao adicional: terraform.tfvars e terraform.tfstate
       reais do import de 2026-08-04 nao localizados em itcenter-edge-01
       nem em copia conhecida
T+20 - API key do usuario IAM terraform-provisioner (criada em
       2026-08-04) tambem dada como perdida
T+25 - Bloqueio registrado em docs/deployment/KNOWN_ISSUES.md e como
       pendencia explicita da EPIC 15 em docs/development/TASKS.md
```

## Causa raiz

Mesmo padrao do INCIDENTE 018 (perda de acesso administrativo sem plano de backup), aqui na camada da conta Oracle Cloud em vez da chave SSH: um unico usuario administrador da tenancy, com um unico fator de MFA, sem fator de backup nem segundo administrador cadastrado. Nao havia redundancia de acesso administrativo na nuvem, apenas na VM.

## Correcao aplicada

Nenhuma — bloqueio em aberto. Nao ha acao possivel sem recuperar o acesso ao Console Oracle Cloud primeiro (fator de backup na tela de login, um segundo administrador existente na tenancy, ou Service Request com o suporte Oracle provando titularidade da conta).

## Como validar

```text
Tentar login no Console Oracle Cloud (https://cloud.oracle.com) com o
usuario administrador conhecido — segue bloqueado no MFA ate a
recuperacao ser concluida.
```

## Licoes aprendidas

* O mesmo tipo de single point of failure do INCIDENTE 018 (credencial administrativa sem backup) pode existir em mais de uma camada ao mesmo tempo — aqui na conta cloud, nao apenas na chave SSH da VM. A licao do INCIDENTE 018 nao havia sido generalizada para a conta Oracle Cloud.
* Artefatos de estado sensiveis (`terraform.tfstate`, `terraform.tfvars`, API keys de automacao) tambem podem se perder por falta de copia de backup, agravando o mesmo tipo de risco em outra camada — o Terraform da EPIC 15 ficou sem state local rastreavel e sem credencial de automacao ao mesmo tempo em que o acesso humano ao Console ficou bloqueado.
* MFA sem fator de backup e sem segundo administrador transforma qualquer perda de dispositivo em bloqueio total, nao apenas inconveniente.

## Melhorias futuras

* Recuperar o acesso ao Console OCI (fator de backup na tela de login, um segundo administrador existente, ou Service Request com o suporte Oracle).
* Apos recuperado: cadastrar um segundo usuario administrador e um fator de MFA de backup, para nao repetir esse bloqueio.
* Gerar uma API key nova para `terraform-provisioner` e refazer a descoberta/import do Terraform do zero (`infra/terraform/README.md`), ja que o state de 2026-08-04 nao foi localizado.
* Guardar copias de `terraform.tfstate`/`terraform.tfvars` em um local seguro fora da VM (cofre de senhas ou storage cifrado), nao apenas localmente.
* Tratar recuperacao de acesso administrativo (SSH e conta cloud) como uma unica categoria de risco operacional, revisada em conjunto, em vez de dois incidentes isolados.

## Automacao recomendada

```text
Nao ha checagem tecnica automatizavel para MFA de conta cloud a partir
do dashboard operacional. Mitigar via processo: checklist periodico
(ex.: trimestral) confirmando que existe segundo administrador ativo,
fator de MFA de backup cadastrado, e copia de backup de chaves
SSH/API keys/terraform.tfstate fora do unico ponto de falha atual.
```

# INCIDENTE 023

## Resumo

Deploy em producao (`Deploy Production #21`) falhou durante o build da imagem do frontend: a sessao SSH que carrega o script remoto de deploy caiu (`client_loop: send disconnect: Broken pipe`, exit code 255) logo apos o Next.js entrar em "Creating an optimized production build...". Causa raiz **nao confirmada** — hipotese mais provavel e pressao de memoria na VM, mas nao foi possivel diagnosticar em tempo real por falta de acesso SSH manual funcional (achado a parte, ver "Licoes aprendidas").

## Severidade

```text
Media
```

## Data

```text
2026-08-17
```

## Ambiente

```text
Producao
GitHub Actions (.github/workflows/deploy-production.yml)
Oracle Cloud VM itcenter-edge-01
```

## Sintomas

Log do job "Deploy to Oracle VM" (run 32052153823, 7m 22s):

```text
1. backup.sh: sucesso ("Backup criado", retencao aplicada)
2. preflight-production.sh: todos os checks OK, incluindo
   "OK Memoria disponivel 352MB" (ja abaixo do MEM_WARN_MB=512,
   acima do MEM_FAIL_MB=256 - preflight nao falha nesse caso)
3. docker compose build: backend usa cache em todas as camadas
   (rapido); frontend chega a "Creating an optimized production
   build ..." (Next.js 16.2.12, Turbopack)
4. Conexao cai: "client_loop: send disconnect: Broken pipe"
5. "Error: Process completed with exit code 255."
```

O job nunca chegou a rodar `docker compose ... up -d` nem o novo gate do Docker Scout (EPIC 29, `962e7ca`) — a falha ocorre antes desses passos, no build em si.

## Impacto

* Deploy da EPIC 29 (correcao de backup/restore/gate de CVE) nao foi aplicado em producao nesta tentativa.
* **Sem indisponibilidade**: como o build falhou antes do `up -d`, os containers da versao anterior (`postgres`, `backend`, `frontend`, `nginx`) continuaram rodando normalmente durante e depois da falha.
* Bloqueia qualquer deploy futuro ate a causa ser confirmada e corrigida (ou ate se confirmar que foi um pico transitorio).

## Linha do tempo

```text
T+00 - Deploy disparado via workflow_dispatch (commit 962e7ca)
T+00 - backup.sh concluido com sucesso
T+00 - preflight-production.sh: OK em todos os checks, memoria
       disponivel reportada em 352MB
T+00 - docker compose build inicia (backend + frontend em paralelo,
       via Compose Bake - "load local bake definitions")
T+00 - build do backend conclui rapido (todas as camadas em cache)
T+~1m - build do frontend chega em "Creating an optimized
        production build ..." (etapa mais pesada de CPU/memoria
        do Next.js/Turbopack)
T+7m22s - sessao SSH cai (Broken pipe), job falha com exit 255
```

## Causa raiz

**Nao confirmada.** Hipotese mais provavel, dado o padrao do erro (queda de conexao durante a etapa historicamente mais pesada de memoria do pipeline) e o contexto ja documentado do projeto:

* A VM (`itcenter-edge-01`) e Oracle Free Tier de 1GB de RAM.
* Desde a EPIC 21 (2026-08-15), 4 containers de observabilidade (`node_exporter`, `cadvisor`, `prometheus`, `grafana`) ficam **ativos continuamente** por decisao registrada em `docs/deployment/KNOWN_ISSUES.md` ("Observabilidade: memoria em alerta com o profile ativo") - a mesma validacao ja havia medido 424MB disponiveis com esses 4 servicos ativos e nada mais rodando.
* O preflight desta tentativa mediu 352MB disponiveis **antes mesmo do build comecar** - menos ainda do que os 424MB da validacao da EPIC 21.
* `npm run build` do Next.js com Turbopack e conhecido por picos de memoria elevados; rodar isso com uma base ja consumida por 4 containers extras e um cenario nunca testado sob carga real ate esta tentativa.

Nao foi possivel confirmar via `free -h`/`dmesg`/`docker stats` no momento da falha porque nao havia acesso SSH manual funcional disponivel para diagnostico em tempo real (ver proximo item).

## Correcao aplicada

Nenhuma ainda - causa raiz nao confirmada, nenhuma mudanca de codigo foi feita em resposta a este incidente.

## Como validar

```text
Diagnostico pendente. Requer uma das duas vias:
1. Acesso SSH manual funcional na VM (free -h, docker stats,
   dmesg -T | grep -i oom durante um novo build) - hoje
   indisponivel, ver Licoes aprendidas.
2. Workflow temporario reaproveitando o secret PROD_SSH_PRIVATE_KEY
   (mesmo padrao usado na recuperacao do INCIDENTE 018) para rodar
   os mesmos comandos de diagnostico via GitHub Actions.
```

## Licoes aprendidas

* A decisao da EPIC 21 de manter a observabilidade ativa continuamente "por ora" (risco ja aceito e documentado) nunca havia sido testada sob a carga real de um build de deploy - este e o primeiro deploy de producao desde que os 4 containers passaram a rodar 24/7, e a memoria disponivel no preflight (352MB) ja veio mais baixa que a da propria validacao da EPIC 21 (424MB).
* **Achado a parte, descoberto durante a tentativa de diagnosticar este incidente**: a chave de acesso SSH manual "de emergencia" (`daniel-manual-access-itcenter-edge-01`) esta incompleta - apenas a chave publica foi localizada salva localmente (`C:\Users\infra\.ssh\daniel-manual-access-itcenter-edge-01.txt`, 118 bytes, confirmado ser so a chave publica pelo cabecalho `ssh-ed25519`); a chave privada correspondente nao foi encontrada em nenhuma pasta comum do usuario. Isso repete o padrao do INCIDENTE 018 (acesso administrativo sem copia de backup) numa forma mais branda: desta vez descoberto ao tentar diagnosticar um problema nao-critico, nao no meio de uma emergencia real. Continua dependendo inteiramente do secret `PROD_SSH_PRIVATE_KEY` do GitHub Actions para qualquer acesso SSH funcional a `itcenter-edge-01`.

## Atualizacao (2026-08-20) - segunda ocorrencia, mesma assinatura

Uma nova tentativa de `Deploy Production` via GitHub Actions falhou de novo com a mesma assinatura exata (`client_loop: send disconnect: Broken pipe`, exit 255, durante `npm run build` do frontend) - preflight mediu **296MB disponiveis**, abaixo dos 352MB desta primeira ocorrencia e dos 424MB da validacao da EPIC 21. Ver `docs/deployment/DEPLOYMENT_HISTORY.md` (entrada de 2026-08-20, "Segunda tentativa de deploy falha de novo por memoria").

Isso confirma o padrao como recorrente, nao um pico isolado: memoria disponivel no preflight caindo em tentativas sucessivas (424 -> 352 -> 296MB), sempre no mesmo ponto de falha. A causa raiz (pressao de memoria durante o build, agravada pela observabilidade sempre ativa) passa de "suspeita" para "fortemente indicada pelo padrao", ainda sem uma medicao direta de `free -h`/`docker stats` durante o build em si (nenhuma das duas ocorrencias teve uma sessao manual acompanhando o momento exato da falha).

Nota tambem que o acesso SSH manual mencionado como indisponivel em "Como validar" abaixo foi recuperado em 2026-08-19 (sessao separada, ver `docs/deployment/DEPLOYMENT_HISTORY.md`) - o diagnostico em tempo real deixou de estar bloqueado por falta de acesso; so nao foi feito ainda porque nenhuma das duas ocorrencias teve uma sessao manual observando o momento exato do build.

## Melhorias futuras

* Rodar o diagnostico pendente (ver "Como validar") na proxima tentativa de deploy, antes de aplicar qualquer mitigacao especulativa.
* Se confirmado que e pressao de memoria: avaliar pausar o profile `observability` durante o `build` do deploy (parar antes, subir de novo depois do `up -d`), desativar o build paralelo do Compose Bake (`COMPOSE_BAKE=false`) para reduzir o pico de memoria simultaneo de backend+frontend, ou aumentar o swap da VM.
* Gerar um novo par de chaves para acesso manual administrativo e guardar a chave privada num cofre de senhas (nao so localmente) - fechar a mesma lacuna do INCIDENTE 018, desta vez antes de precisar dela numa emergencia real.
* Considerar adicionar uma checagem de memoria disponivel tambem durante o build (hoje o preflight so mede antes do build comecar), para o deploy falhar com uma mensagem clara em vez de um "Broken pipe" opaco.

## Automacao recomendada

```text
Nenhuma diretamente aplicavel ainda sem confirmar a causa raiz.
Se confirmado que e memoria: adicionar um check de memoria minima
tambem apos o build (nao so no preflight), e considerar expor o
uso de memoria do build no proprio log do deploy (ex.: `free -h`
antes e depois do `docker compose build`) para futuras falhas
serem diagnosticaveis a partir do proprio log do GitHub Actions,
sem depender de acesso SSH manual.
```

---

# Analise consolidada de causa raiz

## Erros mais recorrentes

* Dependencias de host ausentes.
* Secrets e placeholders ainda nao preparados.
* Permissoes de arquivos sensiveis.
* DNS com propagacao parcial.
* Healthchecks desalinhados do runtime real.
* Recursos limitados da VM.
* Gestao de credenciais e chaves de acesso administrativo sem plano de backup (INCIDENTE 018).
* Seed de dados pos-deploy (usuario admin, configuracao inicial) tratado como implicito em vez de etapa explicita (INCIDENTE 019).
* Esquemas de autenticacao concorrentes disputando o mesmo cabecalho `Authorization` (INCIDENTE 020).
* Tags de imagens externas fixadas no Compose sem confirmar a existencia real no registry (INCIDENTE 021).
* MFA de conta cloud sem fator de backup nem segundo administrador cadastrado (INCIDENTE 022) — mesmo padrao do INCIDENTE 018, em outra camada de acesso administrativo.
* Build de deploy (frontend) coincidindo com pressao de memoria cronica na VM, sem diagnostico possivel por falta de acesso SSH manual funcional (INCIDENTE 023) — causa raiz nao confirmada.

## Causas mais recorrentes

* VM inicial muito enxuta.
* Ordem de deploy dependente de DNS, TLS e secrets.
* Validacoes manuais insuficientes antes do preflight.
* Diferenca entre conectividade interna Docker e conectividade externa.
* Etapas pos-deploy (seed de admin, rotacao/backup de chaves de acesso) sem checklist explicito.
* Servicos ou configuracoes que só rodam sob profile opcional ou cenario raro (ex.: certbot em `maintenance`) escapam da validacao de rotina.

## Erros que poderiam ter sido evitados

* Docker/Compose ausentes poderiam ser detectados por bootstrap.
* Placeholders poderiam ser bloqueados antes do deploy.
* Permissao de `dashboard.htpasswd` poderia ser verificada no preflight.
* Memoria insuficiente poderia ser detectada antes do build.

## Verificacoes obrigatorias antes do deploy

* Docker instalado.
* Docker Compose instalado.
* Usuario com acesso ao Docker.
* `.env.production` criado.
* Secrets reais configurados.
* Dominio propagado.
* Porta 80 aberta.
* Certificados presentes.
* Compose valido.
* Rede Docker declarada.
* Volume persistente declarado.

## Verificacoes automatizaveis

* Presenca de Docker e Compose.
* Validacao de placeholders.
* Validacao de certificado.
* Validacao de portas.
* Validacao de Compose config.
* Validacao de memoria e disco.
* Validacao de healthchecks.
* Smoke tests internos.
* Existencia de ao menos um usuario `admin` ativo apos o deploy (INCIDENTE 019).
* Existencia real das tags de imagens externas no registry, inclusive as usadas somente por profiles opcionais como `maintenance` (INCIDENTE 021).

## Decisoes que evitaram problemas maiores

* Nginx como unico ponto publico.
* PostgreSQL sem porta publica.
* Backend e frontend internos.
* Docker Network isolada.
* Secrets fora do Git.
* Healthchecks no Compose.
* Preflight antes do deploy.
* Isentar de Basic Auth as rotas que a aplicacao ja protege com Bearer token/RBAC (ADR-023), evitando conflito entre os dois esquemas de autenticacao (INCIDENTE 020).

## Mudancas para futuras implantacoes quase automaticas

* Implementar bootstrap versionado.
* Automatizar geracao segura de `.env.production`.
* Automatizar criacao de Basic Auth.
* Automatizar emissao e renovacao TLS.
* Automatizar validacao DNS.
* Adicionar CI com `docker compose config`.
* Adicionar smoke tests completos.
* Adicionar monitoramento e alertas.
* Automatizar o seed idempotente do primeiro admin a partir do `deploy.sh` (INCIDENTE 019).
* Guardar copia de recuperacao de chaves SSH administrativas fora do unico ponto de falha atual (INCIDENTE 018).
* Incluir `docker compose --profile maintenance pull`/`config` no preflight ou em checagem periodica (INCIDENTE 021).
* Cadastrar segundo administrador e fator de MFA de backup na conta Oracle Cloud, e guardar copia de `terraform.tfstate`/`terraform.tfvars`/API keys de automacao fora do unico ponto de falha atual (INCIDENTE 022).
* Diagnosticar pressao de memoria durante builds de deploy (`free -h`/`docker stats` antes e depois do `docker compose build`) e gerar novo par de chaves SSH de acesso manual com a privada guardada em cofre de senhas (INCIDENTE 023).

---

# Playbooks de resposta

## Docker nao sobe

Validar:

```bash
sudo systemctl status docker
docker version
journalctl -u docker --no-pager -n 100
```

Acao:

* Reiniciar Docker.
* Validar permissao do usuario.
* Validar disco e memoria.

## Backend unhealthy

Validar:

```bash
docker logs itcenter-backend
docker exec -it itcenter-backend wget -q -O - http://127.0.0.1:8000/api/v1/health
docker logs itcenter-postgres
```

Acao:

* Conferir `DATABASE_URL`.
* Conferir PostgreSQL healthy.
* Conferir migrations.

## Frontend unhealthy

Validar:

```bash
docker logs itcenter-frontend
docker compose --env-file .env.production -f infra/docker-compose.production.yml exec -T nginx wget -q -O - http://frontend:3000/
```

Acao:

* Conferir build do Next.js.
* Conferir healthcheck.
* Conferir variaveis `ITCENTER_API_BASE_URL`.

## Nginx unhealthy

Validar:

```bash
docker logs itcenter-nginx
docker exec -it itcenter-nginx nginx -t
```

Acao:

* Conferir certificado TLS.
* Conferir `dashboard.htpasswd`.
* Conferir upstreams.

## Banco indisponivel

Validar:

```bash
docker logs itcenter-postgres
docker exec -it itcenter-postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

Acao:

* Conferir variaveis do banco.
* Conferir volume `postgres_data`.
* Conferir disco livre.

## HTTPS invalido

Validar:

```bash
curl -Iv https://itcenter-daniel.chickenkiller.com
ls -l /etc/letsencrypt/live/itcenter-daniel.chickenkiller.com/
```

Acao:

* Conferir dominio.
* Conferir certificado.
* Conferir Nginx.

## Certificado expirado

Validar:

```bash
openssl x509 -in /etc/letsencrypt/live/itcenter-daniel.chickenkiller.com/fullchain.pem -noout -dates
```

Acao:

```bash
docker compose --env-file .env.production -f infra/docker-compose.production.yml --profile maintenance run --rm certbot renew --webroot -w /var/www/certbot
docker compose --env-file .env.production -f infra/docker-compose.production.yml exec nginx nginx -s reload
```

## Dominio nao resolve

Validar:

```bash
dig itcenter-daniel.chickenkiller.com
dig @8.8.8.8 itcenter-daniel.chickenkiller.com
dig @1.1.1.1 itcenter-daniel.chickenkiller.com
dig @9.9.9.9 itcenter-daniel.chickenkiller.com
```

Acao:

* Conferir registro DNS.
* Conferir IP publico.
* Aguardar propagacao quando outros resolvers ja resolvem.

## DNS em propagacao

Validar:

```bash
for dns in 8.8.8.8 1.1.1.1 9.9.9.9; do dig @"$dns" itcenter-daniel.chickenkiller.com; done
```

Acao:

* Nao alterar aplicacao se resolvedores publicos ja resolvem corretamente.
* Aguardar cache do provedor local.

## Healthcheck falhando

Validar:

```bash
docker inspect --format '{{json .State.Health}}' <container>
docker logs <container>
```

Acao:

* Executar o mesmo comando do healthcheck dentro do container.
* Corrigir host, porta ou rota.

## Dashboard inacessivel

Validar:

```bash
curl -I https://itcenter-daniel.chickenkiller.com
docker logs itcenter-nginx
docker logs itcenter-frontend
```

Acao:

* Conferir Basic Auth.
* Conferir Nginx.
* Conferir frontend.

## Agente nao aparece

Validar:

```bash
docker logs itcenter-backend
curl https://itcenter-daniel.chickenkiller.com/api/v1/health
```

Acao:

* Conferir `AGENT_API_KEY`.
* Conferir URL configurada no agente.
* Conferir conectividade da maquina Windows.
* Conferir logs do agente.

## Banco corrompido

Validar:

```bash
docker logs itcenter-postgres
docker exec -it itcenter-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

Acao:

* Parar escrita se necessario.
* Fazer copia do volume antes de tentar reparo.
* Restaurar backup se a corrupcao for confirmada.

## Restore de backup

Validar backup:

```bash
ls -lh /opt/itcenter/backups
```

Executar restore conforme procedimento documentado:

```bash
ITCENTER_RESTORE_CONFIRM=YES sh infra/scripts/restore.sh /opt/itcenter/backups/arquivo.sql.gz
```

## Rollback de deploy

Executar:

```bash
sh infra/scripts/backup.sh
sh infra/scripts/rollback.sh HEAD~1
```

Validar:

```bash
docker compose --env-file .env.production -f infra/docker-compose.production.yml ps
curl -I https://itcenter-daniel.chickenkiller.com
```
