# Diario de implantacao da infraestrutura

> **Historico congelado em 2026-06-26.** Este documento parou de ser atualizado; o historico de deploys continua em `docs/deployment/DEPLOYMENT_HISTORY.md` (inclui os eventos de 2026-06-30 e 2026-07-28, entre outros). Mantido aqui apenas pelo contexto tecnico detalhado do deploy inicial — registre novos deploys em `DEPLOYMENT_HISTORY.md`.

Este documento registra a implantacao da infraestrutura de producao do IT Center Security Cloud na Oracle Cloud.

O objetivo e manter um historico tecnico claro, auditavel e reutilizavel para futuras implantacoes, troubleshooting, onboarding e recuperacao de desastres.

## Contexto

A infraestrutura foi publicada em uma VM Oracle Cloud com Ubuntu Server 24.04 LTS.

O ambiente atual e:

```text
Dominio: itcenter-daniel.chickenkiller.com
IP publico: 147.15.78.220
Cloud: Oracle Cloud
Sistema operacional: Ubuntu Server 24.04 LTS
Runtime: Docker Engine
Orquestracao: Docker Compose
Rede Docker: itcenter-network
Raiz operacional: /opt/itcenter
Aplicacao: /opt/itcenter/app/it-center-security-cloud
Backups: /opt/itcenter/backups
```

Arquitetura implantada:

```text
Internet
    |
    v
DNS: itcenter-daniel.chickenkiller.com
    |
    v
Oracle Cloud VM
    |
    v
Docker Engine
    |
    v
itcenter-network
    |-- PostgreSQL
    |-- FastAPI Backend
    |-- Next.js Dashboard
    `-- Nginx Reverse Proxy
```

## Legenda de status

Cada etapa do diario usa um dos seguintes status:

```text
Sucesso  - etapa concluida e validada
Parcial  - etapa funcionou, mas exigiu ajuste posterior
Falha    - etapa falhou e exigiu correcao
```

## Diario cronologico

### 1. Provisionamento da VM Oracle Cloud

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Criar o servidor base para hospedar a infraestrutura de producao.

Comandos executados:

```text
Etapa executada pelo painel da Oracle Cloud.
```

Resultado esperado:

```text
VM Ubuntu 24.04 LTS acessivel por SSH e com IP publico associado.
```

Resultado obtido:

```text
VM criada e utilizada como Edge Node do MVP.
```

Problemas encontrados:

```text
Nenhum problema critico registrado.
```

Causa raiz:

```text
Nao aplicavel.
```

Correcao aplicada:

```text
Nao aplicavel.
```

Motivo da correcao:

```text
Nao aplicavel.
```

Licoes aprendidas:

* Manter um unico Edge Node reduz custo e complexidade no MVP.
* A Oracle Cloud Free Tier e suficiente para validar a arquitetura inicial.

Proximos passos:

* Instalar Docker Engine.
* Instalar Docker Compose.

### 2. Instalacao do Docker Engine

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Instalar o runtime de containers responsavel por executar PostgreSQL, backend, frontend e Nginx.

Comandos executados:

```bash
docker --version
```

Resultado esperado:

```text
Docker instalado e disponivel no sistema.
```

Resultado obtido:

```text
Docker Engine instalado e validado.
```

Problemas encontrados:

```text
Nenhum problema critico registrado.
```

Causa raiz:

```text
Nao aplicavel.
```

Correcao aplicada:

```text
Nao aplicavel.
```

Motivo da correcao:

```text
Nao aplicavel.
```

Licoes aprendidas:

* Validar `docker --version` imediatamente evita confundir falha de Docker com falha de Compose.

Proximos passos:

* Instalar Docker Compose.

### 3. Instalacao do Docker Compose

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Instalar a ferramenta de orquestracao usada para subir a stack de producao.

Comandos executados:

```bash
docker compose version
```

Resultado esperado:

```text
Docker Compose disponivel como plugin do Docker.
```

Resultado obtido:

```text
Docker Compose instalado e validado.
```

Problemas encontrados:

```text
Nenhum problema critico registrado.
```

Causa raiz:

```text
Nao aplicavel.
```

Correcao aplicada:

```text
Nao aplicavel.
```

Motivo da correcao:

```text
Nao aplicavel.
```

Licoes aprendidas:

* O projeto deve usar Docker Compose v2.
* Compose e suficiente para o MVP e evita overengineering.

Proximos passos:

* Adicionar o usuario `ubuntu` ao grupo `docker`.

### 4. Configuracao do usuario `ubuntu` no grupo Docker

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Permitir que o usuario operacional execute comandos Docker.

Comandos executados:

```bash
sudo usermod -aG docker ubuntu
```

Resultado esperado:

```text
Usuario ubuntu autorizado a executar Docker.
```

Resultado obtido:

```text
Permissao configurada.
```

Problemas encontrados:

```text
Pode ser necessario abrir uma nova sessao SSH para o grupo ser carregado.
```

Causa raiz:

```text
Grupos Linux sao carregados no inicio da sessao.
```

Correcao aplicada:

```text
Abrir nova sessao SSH quando necessario.
```

Motivo da correcao:

```text
Garantir que a permissao do grupo docker esteja ativa.
```

Licoes aprendidas:

* Sempre validar permissoes Docker apos alterar grupos.

Proximos passos:

* Configurar chave SSH da Oracle VM.

### 5. Configuracao da chave SSH da Oracle VM

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Permitir clone seguro do repositorio privado no GitHub.

Comandos executados:

```bash
ssh -T git@github.com
```

Resultado esperado:

```text
GitHub reconhecendo a chave SSH da VM.
```

Resultado obtido:

```text
Clone via SSH habilitado.
```

Problemas encontrados:

```text
Sem a chave cadastrada, o clone privado nao funciona.
```

Causa raiz:

```text
Repositorio privado exige autenticacao.
```

Correcao aplicada:

```text
Chave SSH da VM cadastrada no GitHub.
```

Motivo da correcao:

```text
Evitar uso de senha ou token manual no servidor.
```

Licoes aprendidas:

* SSH e o melhor caminho para clone operacional de repositorio privado.

Proximos passos:

* Clonar o repositorio em `/opt/itcenter/app/it-center-security-cloud`.

### 6. Clone do repositorio privado

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Baixar a aplicacao e os arquivos de infraestrutura na VM.

Comandos executados:

```bash
git clone git@github.com:DanielAzeved0/it-center-security-cloud.git
```

Resultado esperado:

```text
Repositorio clonado com sucesso.
```

Resultado obtido:

```text
Repositorio clonado via SSH.
```

Problemas encontrados:

```text
Nenhum problema critico apos a configuracao da chave SSH.
```

Causa raiz:

```text
Nao aplicavel.
```

Correcao aplicada:

```text
Nao aplicavel.
```

Motivo da correcao:

```text
Nao aplicavel.
```

Licoes aprendidas:

* Validar SSH antes do clone separa problema de autenticacao de problema de rede.

Proximos passos:

* Criar `.env.production`.

### 7. Configuracao do `.env.production`

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Criar o arquivo de ambiente de producao com valores reais e seguros.

Comandos executados:

```bash
cp .env.production.example .env.production
openssl rand -hex 32
```

Resultado esperado:

```text
.env.production criado sem placeholders.
```

Resultado obtido:

```text
Arquivo criado e configurado.
POSTGRES_PASSWORD gerado.
AGENT_API_KEY gerado.
```

Problemas encontrados:

```text
Valores do example nao podem permanecer em producao.
```

Causa raiz:

```text
.env.production.example e apenas template.
```

Correcao aplicada:

```text
Geracao de secrets com openssl rand -hex 32.
```

Motivo da correcao:

```text
Evitar senha previsivel e chave de agente fraca.
```

Licoes aprendidas:

* Preflight deve bloquear placeholders.
* Secrets nunca devem ser commitados.

Proximos passos:

* Criar credencial HTTP Basic do dashboard.

### 8. Criacao do `.secrets/dashboard.htpasswd`

Status:

```text
Parcial
```

Data:

```text
2026-06-26
```

Objetivo:

Proteger o dashboard com HTTP Basic Auth.

Comandos executados:

```bash
mkdir -p .secrets
docker run --rm httpd:2.4-alpine htpasswd -Bbn admin 'SENHA_FORTE_AQUI' > .secrets/dashboard.htpasswd
```

Resultado esperado:

```text
Arquivo .secrets/dashboard.htpasswd criado e legivel pelo Nginx.
```

Resultado obtido:

```text
Arquivo criado, mas posteriormente houve problema de permissao.
```

Problemas encontrados:

```text
Permission denied no dashboard.htpasswd.
```

Causa raiz:

```text
Permissoes do arquivo ou da pasta .secrets impediam leitura pelo container Nginx.
```

Correcao aplicada:

```bash
chmod 700 .secrets
chmod 644 .secrets/dashboard.htpasswd
```

Motivo da correcao:

```text
Permitir leitura pelo Nginx sem expor o secret.
```

Licoes aprendidas:

* Criar secret nao basta; permissoes tambem precisam entrar no checklist.

Proximos passos:

* Validar Docker Compose de producao.

### 9. Validacao do `docker-compose.production.yml`

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Validar a definicao da stack de producao.

Comandos executados:

```bash
docker compose --env-file .env.production -f infra/docker-compose.production.yml config
```

Resultado esperado:

```text
Compose valido e sem erro de sintaxe.
```

Resultado obtido:

```text
Compose validado.
```

Problemas encontrados:

```text
Nenhum problema critico apos configurar o .env.production.
```

Causa raiz:

```text
Nao aplicavel.
```

Correcao aplicada:

```text
Nao aplicavel.
```

Motivo da correcao:

```text
Nao aplicavel.
```

Licoes aprendidas:

* `docker compose config` deve ser executado antes de build e up.

Proximos passos:

* Criar e executar o preflight.

### 10. Criacao do preflight de producao

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Automatizar validacoes obrigatorias antes do deploy.

Comandos executados:

```bash
sh infra/scripts/preflight-production.sh
```

Resultado esperado:

```text
Validar Docker, Compose, memoria, disco, env, secrets, dominio, TLS, volumes, rede, portas e compose config.
```

Resultado obtido:

```text
Preflight criado e usado como gate operacional.
```

Problemas encontrados:

```text
Algumas validacoes dependem de DNS e TLS ja estarem preparados.
```

Causa raiz:

```text
Let's Encrypt depende de DNS e porta 80 funcionando.
```

Correcao aplicada:

```text
Separar preparacao de dominio/certificado da subida final.
```

Motivo da correcao:

```text
Evitar deploy final com Nginx sem certificado valido.
```

Licoes aprendidas:

* Preflight deve falhar cedo e explicar exatamente o que falta.

Proximos passos:

* Criar script de deploy.

### 11. Criacao do script de deploy

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Padronizar o deploy de producao.

Comandos executados:

```bash
sh infra/scripts/deploy.sh
```

Resultado esperado:

```text
Executar preflight, build, up, healthchecks, smoke tests e mostrar URLs finais.
```

Resultado obtido:

```text
Deploy automatizado criado e utilizado.
```

Problemas encontrados:

```text
Healthcheck do frontend exigiu ajuste posterior.
```

Causa raiz:

```text
O alvo inicial do healthcheck nao refletia corretamente o runtime do Next.js no container.
```

Correcao aplicada:

```text
Healthcheck ajustado.
```

Motivo da correcao:

```text
Garantir que o Compose marque o frontend como healthy apenas quando ele responder corretamente.
```

Licoes aprendidas:

* Healthcheck precisa ser validado de dentro do container.

Proximos passos:

* Construir containers.
* Executar smoke tests.

### 12. Build dos containers

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Construir as imagens de producao.

Comandos executados:

```bash
docker compose --env-file .env.production -f infra/docker-compose.production.yml build
```

Resultado esperado:

```text
Imagens de backend e frontend construidas.
```

Resultado obtido:

```text
Build executado.
```

Problemas encontrados:

```text
Pouca memoria da VM exigiu criacao de Swap.
```

Causa raiz:

```text
Limite de recursos da Oracle Cloud Free Tier.
```

Correcao aplicada:

```text
Criacao de Swap na VM.
```

Motivo da correcao:

```text
Estabilizar builds e execucao dos containers.
```

Licoes aprendidas:

* VM pequena precisa de margem de memoria ou Swap.

Proximos passos:

* Subir containers.

### 13. Criacao da rede Docker `itcenter-network`

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Isolar os servicos internos em uma rede Docker nomeada.

Comandos executados:

```bash
docker network ls
docker network inspect itcenter-network
```

Resultado esperado:

```text
Rede criada pelo Docker Compose.
```

Resultado obtido:

```text
Rede itcenter-network disponivel.
```

Problemas encontrados:

```text
Nenhum problema critico registrado.
```

Causa raiz:

```text
Nao aplicavel.
```

Correcao aplicada:

```text
Nao aplicavel.
```

Motivo da correcao:

```text
Nao aplicavel.
```

Licoes aprendidas:

* Rede nomeada facilita troubleshooting.
* Rede isolada evita exposicao direta de backend, frontend e banco.

Proximos passos:

* Validar comunicacao interna.

### 14. Correcao dos healthchecks

Status:

```text
Parcial
```

Data:

```text
2026-06-26
```

Objetivo:

Garantir que cada container seja marcado como healthy somente quando o servico estiver pronto.

Comandos executados:

```bash
docker compose --env-file .env.production -f infra/docker-compose.production.yml ps
docker logs itcenter-frontend
docker compose --env-file .env.production -f infra/docker-compose.production.yml exec -T nginx wget -q -O - http://frontend:3000/
```

Resultado esperado:

```text
PostgreSQL, backend, frontend e Nginx healthy.
```

Resultado obtido:

```text
Frontend inicialmente nao ficou healthy.
```

Problemas encontrados:

```text
Next.js nao respondia corretamente no alvo usado inicialmente pelo healthcheck.
```

Causa raiz:

```text
Healthcheck apontava para alvo inadequado ao contexto interno do container.
```

Correcao aplicada:

```text
Healthcheck do frontend ajustado para usar o hostname interno correto.
```

Motivo da correcao:

```text
Fazer o healthcheck medir disponibilidade real.
```

Licoes aprendidas:

* Um container pode estar funcional e ainda assim ser marcado como unhealthy por healthcheck incorreto.

Proximos passos:

* Reexecutar deploy.
* Validar frontend healthy.

### 15. Validacao do backend

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Confirmar que a API FastAPI responde internamente.

Comandos executados:

```bash
docker exec -it itcenter-backend wget -q -O - http://127.0.0.1:8000/api/v1/health
```

Resultado esperado:

```text
API respondendo healthcheck.
```

Resultado obtido:

```text
Backend respondeu corretamente.
```

Problemas encontrados:

```text
Nenhum problema critico registrado.
```

Causa raiz:

```text
Nao aplicavel.
```

Correcao aplicada:

```text
Nao aplicavel.
```

Motivo da correcao:

```text
Nao aplicavel.
```

Licoes aprendidas:

* `/api/v1/health` e o primeiro ponto de validacao funcional do backend.

Proximos passos:

* Validar Nginx e reverse proxy.

### 16. Configuracao do dominio gratuito

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Apontar um dominio publico para a VM Oracle.

Comandos executados:

```bash
dig itcenter-daniel.chickenkiller.com
nslookup itcenter-daniel.chickenkiller.com
```

Resultado esperado:

```text
Dominio resolvendo para 147.15.78.220.
```

Resultado obtido:

```text
Dominio criado e resolvendo em DNS publicos.
```

Problemas encontrados:

```text
DNS da Vivo demorou a propagar.
```

Causa raiz:

```text
Cache ou atraso de propagacao no resolvedor do provedor.
```

Correcao aplicada:

```text
Testes com Google DNS, Cloudflare e Quad9.
```

Motivo da correcao:

```text
Diferenciar problema externo de DNS de problema da aplicacao.
```

Licoes aprendidas:

* Sempre testar DNS com mais de um resolvedor.

Proximos passos:

* Emitir certificado Let's Encrypt.

### 17. Testes com resolvedores publicos

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Confirmar propagacao DNS fora do provedor local.

Comandos executados:

```bash
dig @8.8.8.8 itcenter-daniel.chickenkiller.com
dig @1.1.1.1 itcenter-daniel.chickenkiller.com
dig @9.9.9.9 itcenter-daniel.chickenkiller.com
```

Resultado esperado:

```text
Google DNS, Cloudflare e Quad9 resolvendo para 147.15.78.220.
```

Resultado obtido:

```text
Resolucao correta nos tres resolvedores.
```

Problemas encontrados:

```text
DNS da Vivo ainda nao propagava.
```

Causa raiz:

```text
Propagacao parcial ou cache do provedor.
```

Correcao aplicada:

```text
Registrar como problema externo ao projeto.
```

Motivo da correcao:

```text
Evitar alteracoes indevidas na infraestrutura quando DNS publico ja estava correto.
```

Licoes aprendidas:

* Falha em um provedor nao implica falha no dominio.

Proximos passos:

* Emitir certificado HTTPS.

### 18. Emissao do certificado Let's Encrypt

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Emitir certificado TLS valido para o dominio.

Comandos executados:

```bash
ls -l /etc/letsencrypt/live/itcenter-daniel.chickenkiller.com/
```

Resultado esperado:

```text
fullchain.pem e privkey.pem presentes.
```

Resultado obtido:

```text
Certificado emitido apos abertura correta da porta 80.
```

Problemas encontrados:

```text
Porta 80 precisava estar acessivel para o desafio HTTP do Let's Encrypt.
```

Causa raiz:

```text
Let's Encrypt precisa validar o dominio por HTTP.
```

Correcao aplicada:

```text
Ajuste na abertura da porta 80.
```

Motivo da correcao:

```text
Permitir validacao do dominio.
```

Licoes aprendidas:

* Antes de emitir TLS, validar DNS e porta 80.

Proximos passos:

* Configurar HTTPS no Nginx.

### 19. Configuracao do Nginx e HTTPS

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Configurar Nginx como reverse proxy com TLS, redirecionamento HTTP para HTTPS e seguranca basica.

Comandos executados:

```bash
docker exec -it itcenter-nginx nginx -t
docker logs itcenter-nginx
curl -I https://itcenter-daniel.chickenkiller.com
```

Resultado esperado:

```text
Nginx carregando certificado e respondendo HTTPS.
```

Resultado obtido:

```text
HTTPS funcionando.
Reverse proxy funcionando.
Headers de seguranca aplicados.
```

Problemas encontrados:

```text
Dependencia correta entre certificado, dominio e Nginx.
```

Causa raiz:

```text
Nginx depende de arquivos reais em /etc/letsencrypt/live/$DOMAIN_NAME.
```

Correcao aplicada:

```text
Certificado emitido antes da subida final do Nginx.
```

Motivo da correcao:

```text
Evitar falha de startup por certificado ausente.
```

Licoes aprendidas:

* TLS deve ser validado no filesystem e por HTTP externo.

Proximos passos:

* Validar Basic Auth.

### 20. Correcao de permissao do `dashboard.htpasswd`

Status:

```text
Falha
```

Data:

```text
2026-06-26
```

Objetivo:

Permitir que Nginx leia o arquivo de Basic Auth.

Comandos executados:

```bash
docker logs itcenter-nginx
ls -la .secrets
chmod 700 .secrets
chmod 644 .secrets/dashboard.htpasswd
```

Resultado esperado:

```text
Nginx lendo .secrets/dashboard.htpasswd.
```

Resultado obtido:

```text
Inicialmente ocorreu Permission denied.
Depois da correcao, o dashboard autenticou normalmente.
```

Problemas encontrados:

```text
Permission denied no dashboard.htpasswd.
```

Causa raiz:

```text
Permissoes inadequadas no arquivo ou diretorio .secrets.
```

Correcao aplicada:

```text
chmod 700 .secrets
chmod 644 .secrets/dashboard.htpasswd
```

Motivo da correcao:

```text
Permitir leitura pelo Nginx sem expor o secret.
```

Licoes aprendidas:

* Erro de autenticacao pode ser causado por permissao de arquivo, nao por senha incorreta.

Proximos passos:

* Validar dashboard com Basic Auth.

### 21. Validacao do Dashboard

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Confirmar acesso ao dashboard protegido por Basic Auth.

Comandos executados:

```bash
curl --user admin:SENHA_FORTE_AQUI https://itcenter-daniel.chickenkiller.com
```

Resultado esperado:

```text
Dashboard acessivel apos autenticacao.
```

Resultado obtido:

```text
Dashboard autenticando normalmente.
```

Problemas encontrados:

```text
Dashboard vazio por ausencia de check-ins do agente.
```

Causa raiz:

```text
Windows Agent integrado ao ambiente publicado apos alinhamento da `AGENT_API_KEY` e correcao de DNS no cliente.
```

Correcao aplicada:

```text
Nenhuma correcao necessaria.
```

Motivo da correcao:

```text
Estado esperado do produto.
```

Licoes aprendidas:

* Dashboard vazio nao significa falha de infraestrutura.

Proximos passos:

* Evoluir e integrar o Windows Agent.

### 22. Testes internos entre containers

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Confirmar comunicacao interna na rede `itcenter-network`.

Comandos executados:

```bash
docker exec -it itcenter-backend wget -q -O - http://127.0.0.1:8000/api/v1/health
docker compose --env-file .env.production -f infra/docker-compose.production.yml exec -T nginx wget -q -O - http://frontend:3000/
docker exec -it itcenter-nginx wget -q -O - http://127.0.0.1/healthz
```

Resultado esperado:

```text
Servicos respondendo internamente.
```

Resultado obtido:

```text
Backend, frontend e Nginx responderam.
```

Problemas encontrados:

```text
Nenhum apos ajustes de healthcheck.
```

Causa raiz:

```text
Nao aplicavel.
```

Correcao aplicada:

```text
Nao aplicavel.
```

Motivo da correcao:

```text
Nao aplicavel.
```

Licoes aprendidas:

* Testes internos eliminam variaveis externas como DNS, navegador e firewall.

Proximos passos:

* Executar smoke tests finais.

### 23. Smoke tests

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Validar os principais componentes apos deploy.

Comandos executados:

```bash
sh infra/scripts/deploy.sh
```

Resultado esperado:

```text
Preflight, build, up, healthchecks e smoke tests aprovados.
```

Resultado obtido:

```text
Ambiente validado.
```

Problemas encontrados:

```text
Nenhum apos correcoes anteriores.
```

Causa raiz:

```text
Nao aplicavel.
```

Correcao aplicada:

```text
Nao aplicavel.
```

Motivo da correcao:

```text
Nao aplicavel.
```

Licoes aprendidas:

* Smoke tests reduzem falso sucesso no deploy.

Proximos passos:

* Validar estado final dos containers.

### 24. Criacao de Swap na Oracle VM

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Compensar pouca memoria disponivel na VM gratuita.

Comandos executados:

```text
Comandos especificos nao registrados.
```

Resultado esperado:

```text
VM mais estavel durante build e execucao dos containers.
```

Resultado obtido:

```text
Containers estabilizados.
```

Problemas encontrados:

```text
Pouca memoria causava risco de instabilidade.
```

Causa raiz:

```text
Limitacao de recursos da Oracle Cloud Free Tier.
```

Correcao aplicada:

```text
Criacao de Swap.
```

Motivo da correcao:

```text
Evitar falhas por falta de memoria.
```

Licoes aprendidas:

* Swap ajuda no MVP, mas nao substitui dimensionamento adequado em producao critica.

Proximos passos:

* Monitorar memoria, disco e swap.

### 25. Estado final da infraestrutura

Status:

```text
Sucesso
```

Data:

```text
2026-06-26
```

Objetivo:

Registrar o estado final da implantacao.

Comandos executados:

```bash
docker ps
docker compose --env-file .env.production -f infra/docker-compose.production.yml ps
curl -I https://itcenter-daniel.chickenkiller.com
```

Resultado esperado:

```text
Infraestrutura funcional e containers saudaveis.
```

Resultado obtido:

```text
PostgreSQL: healthy
Backend: healthy
Frontend: healthy
Nginx: healthy
HTTPS: funcionando
Dashboard: funcionando
Banco: funcionando
Windows Agent: integrado e enviando check-in com 200 OK quando DNS e API key estao corretos
```

Problemas encontrados:

```text
Nenhum problema critico restante na infraestrutura.
```

Causa raiz:

```text
Nao aplicavel.
```

Correcao aplicada:

```text
Nao aplicavel.
```

Motivo da correcao:

```text
Nao aplicavel.
```

Licoes aprendidas:

* Infraestrutura pode estar saudavel mesmo antes de haver dados no dashboard.

Proximos passos:

* Evoluir completamente o Windows Agent.

## Decisoes de arquitetura

### Oracle Cloud

Escolhida por oferecer Free Tier, VM gratuita e recursos suficientes para o MVP.

### Docker

Escolhido para padronizar runtime, reduzir diferencas de ambiente e facilitar reproducao.

### Docker Compose

Escolhido por ser simples, suficiente para o MVP e menos complexo que Kubernetes.

### FastAPI

Escolhido por simplicidade, produtividade, boa performance e contrato HTTP claro.

### PostgreSQL

Escolhido como Data Layer por ser robusto, gratuito, relacional e adequado a inventario, metricas, eventos e alertas.

### Next.js

Escolhido por oferecer base moderna para dashboard web e evolucao futura para SaaS.

### Nginx

Escolhido como reverse proxy, terminador TLS e ponto unico de entrada publica.

### HTTPS obrigatorio

Obrigatorio porque o sistema trafega dados operacionais e de seguranca.

### Basic Auth

Usado como protecao administrativa minima do dashboard no MVP.

### AGENT_API_KEY

Usado para autenticar check-ins automatizados do agente sem exigir sessao de usuario.

### Docker Network isolada

Usada para impedir exposicao direta de PostgreSQL, backend e frontend.

### Reverse Proxy

Usado para centralizar TLS, headers, autenticacao, rate limit e roteamento.

### Health Checks

Usados para medir saude real dos containers e ordenar o startup.

### Deploy automatizado

Usado para reduzir erro humano e tornar a implantacao repetivel.

## Licoes aprendidas

### DNS

Problemas de propagacao DNS podem ocorrer em um provedor mesmo quando resolvedores publicos ja estao corretos.

Validar com:

```bash
dig @8.8.8.8 itcenter-daniel.chickenkiller.com
dig @1.1.1.1 itcenter-daniel.chickenkiller.com
dig @9.9.9.9 itcenter-daniel.chickenkiller.com
```

### Health Checks

Um healthcheck incorreto pode marcar um container funcional como unhealthy.

### Containers unhealthy

Diagnosticar em camadas:

```bash
docker ps
docker logs <container>
docker inspect <container>
docker exec -it <container> sh
```

### Nginx

Falhas de Nginx podem vir de certificado ausente, dominio incorreto, upstream indisponivel ou permissao de secrets.

### Certificados

Validar sempre:

```bash
ls -l /etc/letsencrypt/live/$DOMAIN_NAME/
```

### Comunicacao interna

Testar de dentro dos containers ajuda a separar problema interno de problema externo.

### Docker Compose

Executar antes do deploy:

```bash
docker compose --env-file .env.production -f infra/docker-compose.production.yml config
```

### Preflight

Preflight economiza tempo porque falha antes do build quando algo essencial esta ausente.

### Dashboard vazio

Sem Windows Agent integrado, o dashboard pode estar vazio mesmo com a infraestrutura correta.

## Checklist final de producao

### Host

- [ ] VM criada na Oracle Cloud.
- [ ] Ubuntu 24.04 LTS instalado.
- [ ] IP publico associado.
- [ ] Acesso SSH funcionando.
- [ ] Usuario administrativo definido.
- [ ] Login por chave SSH validado.
- [ ] Hostname revisado.
- [ ] Timezone configurado.
- [ ] Sistema atualizado.
- [ ] Pacotes essenciais instalados.
- [ ] Memoria disponivel validada.
- [ ] Disco livre validado.
- [ ] Swap configurada quando necessario.
- [ ] Firewall do sistema revisado.
- [ ] Security List da Oracle revisada.

### Docker

- [ ] Docker Engine instalado.
- [ ] Docker Compose instalado.
- [ ] `docker --version` executado.
- [ ] `docker compose version` executado.
- [ ] Docker daemon ativo.
- [ ] Usuario `ubuntu` no grupo `docker`.
- [ ] Nova sessao SSH aberta apos alterar grupos.
- [ ] Docker executa sem `sudo`, se aplicavel.
- [ ] Build Docker testado.
- [ ] Docker logs acessiveis.

### Repositorio

- [ ] Chave SSH criada na VM.
- [ ] Chave SSH cadastrada no GitHub.
- [ ] `ssh -T git@github.com` validado.
- [ ] Repositorio privado clonado.
- [ ] Repositorio em `/opt/itcenter/app/it-center-security-cloud`.
- [ ] Branch correta selecionada.
- [ ] Arquivos de infraestrutura presentes.
- [ ] `.gitignore` protege secrets.
- [ ] Nenhum secret commitado.
- [ ] Permissoes do diretorio revisadas.

### Estrutura operacional

- [ ] `/opt/itcenter/app/it-center-security-cloud` existe.
- [ ] `/opt/itcenter/backups` existe.
- [ ] `/opt/itcenter/configs` existe.
- [ ] `/opt/itcenter/runtime` existe.
- [ ] `/opt/itcenter/scripts` existe.
- [ ] `/opt/itcenter/secrets` existe.
- [ ] `/opt/itcenter/logs` existe.
- [ ] `/opt/itcenter/bin` existe.
- [ ] Owner dos diretorios revisado.
- [ ] Permissoes dos diretorios revisadas.

### Ambiente e secrets

- [ ] `.env.production` criado.
- [ ] `.env.production` baseado no example.
- [ ] `DOMAIN_NAME` preenchido.
- [ ] `DOMAIN_NAME` nao e placeholder.
- [ ] `POSTGRES_DB` preenchido.
- [ ] `POSTGRES_USER` preenchido.
- [ ] `POSTGRES_PASSWORD` gerado.
- [ ] `DATABASE_URL` revisado.
- [ ] `AGENT_API_KEY` gerado.
- [ ] `.secrets` criado.
- [ ] `dashboard.htpasswd` criado.
- [ ] Permissao de `.secrets` validada.
- [ ] Permissao de `dashboard.htpasswd` validada.
- [ ] Nenhum secret exibido em logs.

### Rede e DNS

- [ ] Dominio criado.
- [ ] DNS aponta para IP publico.
- [ ] Google DNS resolve.
- [ ] Cloudflare DNS resolve.
- [ ] Quad9 resolve.
- [ ] DNS local testado.
- [ ] Porta 80 liberada.
- [ ] Porta 443 liberada.
- [ ] Porta 22 restrita quando possivel.
- [ ] Porta 3000 nao exposta.
- [ ] Porta 8000 nao exposta.
- [ ] Porta 5432 nao exposta.
- [ ] Rede Docker `itcenter-network` criada.
- [ ] Containers na rede correta.

### TLS e Nginx

- [ ] `/etc/letsencrypt` existe.
- [ ] `fullchain.pem` existe.
- [ ] `privkey.pem` existe.
- [ ] Certificado corresponde ao dominio.
- [ ] Certificado nao expirado.
- [ ] Nginx inicia sem erro.
- [ ] Nginx carrega certificado.
- [ ] HTTP redireciona para HTTPS.
- [ ] HTTPS responde.
- [ ] HSTS ativo.
- [ ] Headers de seguranca presentes.
- [ ] Basic Auth ativo no dashboard.
- [ ] Endpoint do agente sem Basic Auth.
- [ ] Rate limit configurado.
- [ ] Reverse proxy para frontend validado.
- [ ] Reverse proxy para backend validado.

### Docker Compose

- [ ] `docker compose config` valido.
- [ ] `postgres` definido.
- [ ] `backend` definido.
- [ ] `frontend` definido.
- [ ] `nginx` definido.
- [ ] `certbot` definido.
- [ ] Restart policies configuradas.
- [ ] Healthchecks configurados.
- [ ] Volumes revisados.
- [ ] Bind mounts revisados.
- [ ] Apenas Nginx publica portas.
- [ ] `postgres_data` configurado.
- [ ] Rede `itcenter-network` declarada.

### Containers

- [ ] PostgreSQL iniciou.
- [ ] PostgreSQL healthy.
- [ ] Backend iniciou.
- [ ] Backend healthy.
- [ ] Frontend iniciou.
- [ ] Frontend healthy.
- [ ] Nginx iniciou.
- [ ] Nginx healthy.
- [ ] Certbot disponivel.
- [ ] `docker ps` validado.
- [ ] `docker compose ps` validado.
- [ ] Logs sem erros criticos.

### Comunicacao interna

- [ ] Backend acessa PostgreSQL.
- [ ] Migrations aplicadas.
- [ ] Backend `/api/v1/health` responde.
- [ ] Frontend responde internamente.
- [ ] Nginx `/healthz` responde.
- [ ] Nginx acessa frontend.
- [ ] Nginx acessa backend.
- [ ] Frontend consegue chamar backend.
- [ ] Rede interna resolve nomes dos servicos.
- [ ] Smoke tests executados.

### Aplicacao

- [ ] Dashboard acessivel via HTTPS.
- [ ] Dashboard solicita Basic Auth.
- [ ] Basic Auth validado.
- [ ] Backend responde health.
- [ ] Agent API pronta.
- [ ] Dashboard vazio entendido como esperado sem agente.
- [ ] Nenhum endpoint novo exposto indevidamente.
- [ ] Contrato da API preservado.
- [ ] Comportamento do agente preservado.
- [ ] Rotas administrativas protegidas.

### Backup e recuperacao

- [ ] Script de backup existe.
- [ ] Backup manual executado.
- [ ] Arquivo gerado em `/opt/itcenter/backups`.
- [ ] Timestamp no nome do backup.
- [ ] Permissao do backup revisada.
- [ ] Retencao definida.
- [ ] Restore documentado.
- [ ] Restore testado em ambiente seguro.
- [ ] Volume `postgres_data` persistente.
- [ ] Plano de rollback documentado.

### Operacao

- [ ] Logs via stdout/stderr.
- [ ] `docker logs` funciona.
- [ ] Uso de CPU validado.
- [ ] Uso de RAM validado.
- [ ] Uso de disco validado.
- [ ] Uso de swap validado.
- [ ] Containers reiniciam automaticamente.
- [ ] Healthchecks funcionando.
- [ ] Preflight executado.
- [ ] Deploy automatizado executado.
- [ ] Documentacao atualizada.

### Seguranca

- [ ] Secrets fora do Git.
- [ ] Certificados fora do Git.
- [ ] `.env.production` fora do Git.
- [ ] Banco nao exposto.
- [ ] Backend nao exposto.
- [ ] Frontend nao exposto diretamente.
- [ ] Apenas Nginx publico.
- [ ] HTTPS obrigatorio.
- [ ] API Key do agente configurada.
- [ ] Basic Auth configurado.
- [ ] Permissoes de secrets revisadas.
- [ ] Firewall revisado.
- [ ] Security List revisada.
- [ ] Headers de seguranca validados.
- [ ] Rate limit ativo para check-in.

### Documentacao

- [ ] README atualizado.
- [ ] Deployment documentado.
- [ ] HTTPS documentado.
- [ ] Troubleshooting documentado.
- [ ] Known issues documentado.
- [ ] Lessons learned documentado.
- [ ] Arquitetura documentada.
- [ ] Rede documentada.
- [ ] Containers documentados.
- [ ] Seguranca documentada.
- [ ] Diario de implantacao atualizado.

## Proximos passos

O proximo grande bloco do projeto e evoluir o Windows Agent como produto independente.

Objetivos:

* separar do repositorio principal;
* criar instalador;
* criar servico Windows;
* adicionar atualizacao automatica;
* ampliar inventario;
* coletar metricas;
* monitorar processos;
* coletar eventos do Windows;
* integrar Microsoft Defender;
* integrar Firewall;
* inventariar software instalado;
* detectar alteracoes;
* gerar Security Events;
* adicionar telemetria;
* adicionar cache offline;
* adicionar compressao;
* adicionar retry inteligente;
* adicionar criptografia;
* assinar payloads.
