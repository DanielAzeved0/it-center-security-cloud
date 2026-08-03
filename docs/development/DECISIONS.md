# DECISIONS.md

# Registro de Decisões Arquiteturais

## Objetivo

Documentar todas as decisões importantes tomadas durante o desenvolvimento do IT Center Security Cloud.

Este documento deve responder:

* O que foi decidido?
* Por que foi decidido?
* Quais alternativas existiam?
* Quais são os impactos da decisão?

---

# ADR-001

## Data

2026-06-24

## Decisão

O projeto será desenvolvido inicialmente como uma aplicação monolítica.

## Motivo

O objetivo do MVP é validar o produto rapidamente.

Microserviços aumentariam:

* Complexidade
* Custos
* Tempo de desenvolvimento
* Tempo de manutenção

## Alternativas Avaliadas

* Microserviços
* Arquitetura distribuída

## Resultado

Aplicação monolítica.

---

# ADR-002

## Data

2026-06-24

## Decisão

Utilizar Oracle Cloud Free Tier como ambiente principal.

## Motivo

Permite:

* Hospedagem gratuita
* Docker
* Banco PostgreSQL
* HTTPS
* Portfólio profissional

## Alternativas Avaliadas

* AWS
* Azure
* Google Cloud
* VPS paga

## Resultado

Oracle Cloud Free Tier.

---

# ADR-003

## Data

2026-06-24

## Decisão

Utilizar FastAPI como backend principal.

## Motivo

* Simples
* Moderno
* Excelente documentação
* Ótima integração com PostgreSQL
* Muito rápido para MVP

## Alternativas Avaliadas

* ASP.NET Core
* Express.js
* NestJS
* Django

## Resultado

FastAPI.

---

# ADR-004

## Data

2026-06-24

## Decisão

Utilizar PostgreSQL como banco de dados oficial.

## Motivo

* Open Source
* Gratuito
* Escalável
* Compatível com SaaS futuro

## Alternativas Avaliadas

* SQLite
* MySQL
* MariaDB

## Resultado

PostgreSQL.

---

# ADR-005

## Data

2026-06-24

## Decisão

Utilizar PowerShell como agente Windows.

## Motivo

* Presente em praticamente todos os Windows
* Não exige instalação adicional
* Fácil distribuição
* Ideal para ambientes corporativos

## Alternativas Avaliadas

* Python Agent
* C# Agent
* Go Agent

## Resultado

PowerShell.

---

# ADR-006

## Data

2026-06-24

## Decisão

Utilizar Next.js para o Dashboard.

## Motivo

* Moderno
* Excelente para dashboards
* Permite futura evolução para SaaS

## Alternativas Avaliadas

* React puro
* Angular
* Vue

## Resultado

Next.js.

---

# ADR-007

## Data

2026-06-24

## Decisão

Utilizar Docker e Docker Compose desde o início.

## Motivo

* Facilita deploy
* Facilita migração
* Padroniza ambiente

## Alternativas Avaliadas

* Instalação manual
* Scripts Shell

## Resultado

Docker Compose.

---

# ADR-008

## Data

2026-06-24

## Decisão

Implementar funcionalidades de SOC de forma gradual.

## Motivo

O objetivo principal do MVP é:

* Inventário
* Monitoramento
* Observabilidade

SOC avançado será implementado em etapas.

## Alternativas Avaliadas

* Wazuh desde o início
* SIEM completo desde o início

## Resultado

SOC Light no MVP.

---

# ADR-009

## Data

2026-06-24

## Decisão

Utilizar ASSET_POLICY.md como fonte de verdade para validação de softwares autorizados.

## Motivo

Evitar falsos positivos.

Exemplo:

RustDesk é utilizado legitimamente pela equipe de TI.

## Alternativas Avaliadas

* Lista fixa de softwares proibidos
* Regras rígidas sem contexto

## Resultado

Validação baseada em política.

---

# ADR-010

## Data

2026-06-24

## Decisão

O sistema não irá coletar dados pessoais ou conteúdo de usuários.

## Motivo

Respeitar privacidade.

Evitar riscos legais.

## Não será coletado

* Senhas
* Cookies
* Histórico de navegação
* Arquivos pessoais
* Conteúdo de documentos
* E-mails

## Resultado

Coleta apenas operacional.

---

# ADR-011

## Data

2026-06-24

## Decisão

Toda nova funcionalidade deverá possuir documentação antes da implementação.

## Motivo

Evitar retrabalho.

Garantir padronização.

Facilitar manutenção.

## Resultado

Fluxo obrigatório:

Planejamento
↓
Documentação
↓
Implementação
↓
Teste
↓
Deploy

---

# ADR-012

## Data

2026-06-24

## Decisão

O repositório permanecerá privado durante o desenvolvimento inicial.

## Motivo

* Evitar exposição de código incompleto
* Evitar vazamento de informações internas
* Permitir mudanças arquiteturais sem impacto

## Critério para Tornar Público

* MVP concluído
* Documentação concluída
* Secrets removidos
* Dados corporativos removidos

## Resultado

Repositório privado inicialmente.

---

# Modelo para Novas Decisões

---

# ADR-013

## Data

2026-06-24

## Decisão

Integrar a API FastAPI diretamente ao PostgreSQL usando o driver psycopg.

## Motivo

O projeto já concluiu a criação do banco e das tabelas iniciais.

Manter repositórios em memória impediria o MVP de cumprir o critério de sucesso:

* A API salvar dados.
* O PostgreSQL armazenar dados.
* O dashboard consultar dados persistidos futuramente.

## Alternativas Avaliadas

* Continuar com repositórios em memória temporários.
* Usar SQLAlchemy desde o início.
* Usar psycopg diretamente.

## Resultado

Usar psycopg diretamente no MVP.

Impactos:

* Menos dependências e menor complexidade inicial.
* Queries SQL explícitas e alinhadas ao docs/backend/DATABASE.md.
* Possibilidade de migrar para SQLAlchemy futuramente se o domínio crescer.

---

# ADR-014

## Data

2026-06-25

## Decisão

Rodar o ambiente local completo com Docker Compose, incluindo PostgreSQL, backend FastAPI e frontend Next.js.

O backend deverá aplicar as migrations automaticamente antes de iniciar a API quando executado em container.

## Motivo

Durante a execução local, rodar banco, migration, backend e dashboard manualmente gerou atrito e erros de ambiente, como:

* `psql` ausente no Windows.
* `python` sem alias no CMD.
* backend desligado enquanto o dashboard tentava consumir a API.
* necessidade de lembrar a ordem correta de inicialização.

O Compose reduz esse atrito e mantém o fluxo coerente com a stack oficial já aprovada no ADR-007.

## Alternativas Avaliadas

* Continuar com execução manual de cada serviço.
* Criar scripts `.cmd` locais.
* Rodar apenas o PostgreSQL em Docker.
* Rodar PostgreSQL, backend e frontend em Docker Compose.

## Resultado

Usar `infra/docker-compose.yml` como entrada principal para desenvolvimento local integrado.

Comando oficial local:

```powershell
docker compose -f infra/docker-compose.yml up --build
```

Impactos:

* Menos dependência de Python, Node e psql instalados no host.
* Migrations aplicadas de forma previsível no startup do backend.
* Dashboard aponta para o backend pelo DNS interno `backend`.
* Nginx continua reservado para produção/cloud, não para o fluxo local inicial.

---

# ADR-015

## Data

2026-06-25

## Decisao

Adotar Docker Scout como gate de seguranca para imagens locais e tratar vulnerabilidades critical/high antes de publicar o ambiente.

O backend passa a usar base Alpine para reduzir superficie de vulnerabilidades. A base atual de producao e `python:3.13-alpine`.

O frontend passa a usar Next.js `16.2.9`, `picomatch` `4.0.4` fixo e um patch de build para substituir o `picomatch` compilado dentro do Next quando necessario.

A imagem final do frontend remove o `npm` global e inicia o Next.js diretamente com `node`, porque o Docker Scout detectava `picomatch 4.0.3` dentro das dependencias internas do npm empacotado pela imagem base `node:22-alpine`.

O PostgreSQL permanece em `postgres:16-alpine`, com risco residual documentado quando a CVE vier da imagem oficial e ainda nao houver tag corrigida.

## Motivo

As varreduras iniciais apontaram:

* `infra-backend:latest` com CVEs critical/high vindas da base Debian.
* `infra-frontend:latest` com CVEs high em Next.js e `picomatch`.
* `postgres:16-alpine` com CVE residual em pacote da imagem oficial.

Como o produto e de seguranca, imagens com vulnerabilidades corrigiveis nao devem ser normalizadas no fluxo de desenvolvimento.

## Alternativas Avaliadas

* Ignorar alertas ate o deploy em cloud.
* Usar `npm audit fix --force`.
* Trocar backend para base Alpine.
* Atualizar dependencias diretas e documentar risco residual de imagem oficial.

## Resultado

* Backend migrou para Alpine e deve ficar sem critical/high no Scout.
* Frontend atualizou Next.js e corrige `picomatch` no build.
* Frontend remove `npm` global da imagem final para eliminar dependencias de build/runtime nao usadas.
* `npm audit fix --force` nao sera usado sem revisao.
* CVE residual de imagem oficial sera acompanhada como P1 e registrada em `docs/security/SECURITY.md`.

Impactos:

* Build fica mais rigoroso.
* O patch do frontend deve ser removido futuramente quando o Next empacotar `picomatch` corrigido diretamente.
* O deploy externo passa a depender do gate de imagens descrito em `docs/deployment/PRODUCTION.md`.

---

# ADR-016

## Data

2026-06-26

## Decisão

Publicar o MVP em um único nó de borda denominado `itcenter-edge-01`, executando Nginx, frontend, backend e PostgreSQL por Docker Compose.

A VCN da Oracle Cloud usará `10.0.0.0/16`, com subnet pública `10.0.0.0/24` para o nó de borda e subnet privada `10.0.1.0/24` reservada para a futura separação dos serviços.

## Motivo

O MVP precisa de uma topologia simples, gratuita e capaz de receber tráfego HTTPS sem expor os serviços internos. Um único nó reduz custo e operação, enquanto a VCN com subnet privada já preparada evita uma mudança de endereçamento quando a aplicação crescer.

## Alternativas Avaliadas

* Criar uma única subnet e postergar a segmentação de rede.
* Separar frontend, backend e banco em instâncias distintas desde o MVP.
* Usar apenas serviços gerenciados da Oracle Cloud.

## Resultado

* O Nginx é o único serviço publicado nas portas 80 e 443.
* Next.js, FastAPI e PostgreSQL permanecem na rede interna do Docker.
* A subnet privada não hospeda componentes no MVP.
* Em evolução futura, os componentes poderão migrar para a subnet privada, preservando `itcenter-edge-01` como ponto de entrada e proxy reverso.

---

# ADR-017

## Data

2026-06-26

## Decisão

Adotar uma arquitetura operacional em camadas no MVP:

```text
Edge Node
    ↓
Infrastructure Layer
    ↓
Platform Layer
    ↓
Application Layer
    ↓
Data Layer
```

Também ficam definidos:

* Docker Network explícita chamada `itcenter-network`.
* PostgreSQL tratado como Data Layer, separado conceitualmente de frontend/backend.
* Dados do PostgreSQL persistidos em volume nomeado `postgres_data`.
* Configurações, certificados e secrets montados por bind mounts somente leitura quando consumidos pelos containers.
* Logs de containers enviados para `stdout`/`stderr`, sem volumes nomeados de logs no MVP.
* Estrutura operacional do host baseada em `/opt/itcenter`.

## Motivo

O MVP continua simples e barato, rodando em um único Edge Node, mas a arquitetura precisa deixar claro o limite entre infraestrutura, plataforma, aplicação, dados e segurança.

Essa separação reduz ambiguidade operacional e facilita evoluções futuras, como:

* mover PostgreSQL para uma instância privada;
* adicionar Prometheus, Loki, Grafana, Wazuh ou MinIO;
* criar backups previsíveis;
* diagnosticar rede Docker por nome estável;
* coletar logs por ferramentas padrão sem depender de arquivos internos dos containers.

## Alternativas Avaliadas

* Manter a rede gerada automaticamente pelo Docker Compose.
* Tratar PostgreSQL apenas como mais um container da aplicação.
* Criar volumes nomeados para logs de backend, frontend e Nginx.
* Migrar secrets imediatamente para `/opt/itcenter/secrets`.

## Resultado

* `infra/docker-compose.production.yml` passa a nomear explicitamente a rede interna como `itcenter-network`.
* `postgres_data` permanece como volume nomeado oficial para persistência do PostgreSQL.
* Bind mounts de configuração, certificados e credenciais continuam somente leitura no Nginx.
* Logs ficam em `stdout`/`stderr`, compatíveis com `docker logs` e futura coleta por Loki/Promtail.
* `/opt/itcenter/app` é o local oficial do repositório na VM.
* `.env.production` e `.secrets/dashboard.htpasswd` permanecem relativos ao repositório no MVP, preservando compatibilidade com Compose e preflight.

Impactos:

* A arquitetura fica preparada para separar serviços sem mudar o desenho geral.
* A operação ganha nomes estáveis para rede, dados e diretórios.
* Não há aumento relevante de complexidade no MVP.

---

# ADR-018

## Data

2026-06-26

## Decisao

Refatorar a infraestrutura de producao para usar uma camada operacional versionada com:

* Dockerfiles revisados para imagens menores e runtime mais enxuto.
* `docker-compose.production.yml` com healthchecks, `depends_on` por saude e hardening basico.
* Nginx com headers de seguranca, timeouts, endpoint interno de health e ajustes de proxy.
* Scripts oficiais para preflight, deploy, rollback, backup e restore.
* Estrutura do host `/opt/itcenter` expandida com `runtime` e `bin`.

## Motivo

O MVP precisa continuar simples e barato, mas o ambiente de producao deve ser reproduzivel, verificavel e seguro o bastante para operar na Oracle Cloud sem depender de comandos manuais.

## Alternativas Avaliadas

* Continuar usando apenas comandos manuais de Docker Compose.
* Adicionar uma ferramenta externa de orquestracao desde ja.
* Migrar para Kubernetes antes do MVP estar validado.
* Manter Compose v2 com scripts versionados e hardening incremental.

## Resultado

Manter Docker Compose v2 como plataforma de producao do MVP e adicionar automacao operacional simples em `infra/scripts`.

Impactos:

* Deploy passa por preflight antes de subir containers.
* Rollback preserva o banco e troca somente a versao da aplicacao.
* Backup/restore ficam padronizados.
* Nginx reduz superficie de informacao exposta.
* A arquitetura segue pronta para futura observabilidade com Prometheus, Loki e Grafana sem adotar overengineering agora.

---

# ADR-019

## Data

2026-06-26

## Decisao

Formalizar os contratos operacionais minimos da producao:

* Preflight de producao obrigatorio antes do deploy.
* Scripts operacionais versionados em `infra/scripts`.
* Logs de containers em `stdout`/`stderr`.
* PostgreSQL como Data Layer do MVP.
* Rede Docker explicita `itcenter-network`.

## Motivo

O projeto deve continuar simples, mas precisa de operacao repetivel e auditavel. Esses contratos reduzem risco sem adicionar ferramentas externas ou complexidade desnecessaria.

## Alternativas Avaliadas

* Continuar com comandos manuais.
* Criar volumes de logs por servico.
* Usar rede Docker gerada automaticamente.
* Tratar PostgreSQL como detalhe interno do backend.
* Adotar plataforma de observabilidade antes do MVP estar publicado.

## Resultado

* `preflight-production.sh` valida Docker, Compose, secrets, dominio, TLS, portas e Compose antes do deploy.
* `deploy.sh` e `backup.sh` sao as entradas operacionais principais para publicacao e backup.
* Containers continuam escrevendo logs em `stdout`/`stderr`, compativeis com `docker logs` e futura coleta por Loki/Promtail.
* PostgreSQL permanece isolado na rede interna e persistido em `postgres_data`.
* `itcenter-network` e o nome oficial da rede de producao, facilitando troubleshooting e evolucao futura.

Impactos:

* Nenhuma porta de PostgreSQL, backend ou frontend e exposta publicamente.
* Apenas o Nginx publica `80` e `443`.
* O deploy fica mais previsivel apos reboot da VM.
* Observabilidade futura pode ser adicionada sem mudar o contrato de logs.

---

# ADR-020

## Data

2026-06-29

## Decisao

Adicionar GitHub Actions para CI automatico e deploy manual de producao via SSH.

## Motivo

O deploy ja possui scripts versionados (`preflight-production.sh`, `deploy.sh`, `backup.sh` e `rollback.sh`), mas a execucao ainda depende de comandos manuais fora de um fluxo auditavel. GitHub Actions permite validar pull requests, registrar historico de execucao e acionar deploy controlado sem mover os secrets da aplicacao para o repositorio.

## Alternativas Avaliadas

* Continuar com deploy manual por SSH.
* Fazer deploy automatico em todo push na `main`.
* Usar GitHub Actions com acionamento manual para producao.

## Resultado

* `CI` roda testes do backend, build do frontend e validacao de Docker Compose.
* `Deploy Production` roda apenas por `workflow_dispatch`.
* A action acessa a VM via SSH, atualiza o repositorio, executa backup e chama `MIN_MEM_MB=256 sh infra/scripts/deploy.sh`.
* `.env.production`, `.secrets/dashboard.htpasswd` e certificados TLS continuam armazenados na VM, fora do GitHub Actions.

Impactos:

* CI passa a ser o gate minimo antes do deploy.
* O deploy fica auditavel no GitHub, mas ainda exige acionamento humano.
* Deploy automatico em push fica fora do escopo ate a operacao estar mais madura.

---

# ADR-021

## Data

2026-07-03

## Decisao

Adotar RBAC administrativo inicial com tres papeis:

* `admin`
* `analyst`
* `viewer`

A autenticacao de usuarios humanos sera separada da autenticacao do agente Windows.

O agente continuara usando `X-Agent-Api-Key` para check-in. Usuarios administrativos usarao login proprio em etapa futura da EPIC 12, com sessao ou JWT, validacao de usuario ativo, permissao por papel e auditoria de acoes criticas.

## Motivo

O MVP usa HTTP Basic Auth no Nginx para proteger o dashboard, mas esse controle nao oferece governanca suficiente para operacao administrativa:

* nao identifica adequadamente cada usuario no backend;
* nao permite RBAC;
* nao registra auditoria de acoes sensiveis;
* nao diferencia leitura, investigacao e administracao.

Separar autenticacao do agente e autenticacao humana evita misturar dois dominios com riscos e ciclos de vida diferentes.

## Alternativas Avaliadas

* Manter apenas HTTP Basic Auth.
* Usar um unico segredo compartilhado para operadores.
* Implementar login sem RBAC.
* Implementar RBAC inicial com `admin`, `analyst` e `viewer`.
* Unificar API Key do agente com credenciais de usuarios humanos.

## Resultado

O projeto adotara RBAC inicial documentado em `docs/security/AUTH.md`.

Contratos definidos:

* `admin` tem permissao administrativa completa.
* `analyst` pode visualizar dados e resolver alertas, mas nao gerenciar usuarios.
* `viewer` tem acesso somente leitura.
* `users` e `audit_logs` fazem parte da base de governanca administrativa.
* `POST /api/v1/agent/checkin` permanece protegido por `X-Agent-Api-Key`.
* Rotas administrativas serao protegidas por login humano.

Impactos:

* EPIC 12 passa a ter fronteira clara entre governanca administrativa e check-in do agente.
* Proximas tasks podem implementar banco, login e protecao de rotas sem redefinir o modelo de permissao.
* HTTP Basic Auth pode continuar como camada adicional no Nginx, mas nao substitui o login administrativo da aplicacao.

---

# ADR-022

## Data

2026-07-03

## Decisao

Implementar login administrativo com Bearer token assinado por HMAC SHA-256, senha armazenada como PBKDF2-SHA256 e autorizacao server-side por RBAC.

## Motivo

A EPIC 12 precisa substituir o Basic Auth do MVP por um mecanismo em que o backend conheca o usuario humano, valide o status do usuario, aplique permissoes por papel e registre auditoria de acoes criticas.

O projeto ainda nao precisa de SSO, MFA ou provedor externo. Um token assinado localmente atende ao escopo atual sem adicionar dependencia externa.

## Alternativas Avaliadas

* Manter Basic Auth.
* Usar cookie de sessao server-side.
* Usar JWT por biblioteca externa.
* Usar Bearer token assinado localmente com HMAC SHA-256.
* Adotar SSO desde ja.

## Resultado

* `POST /api/v1/auth/login` valida `users.email`, `users.status` e `password_hash`.
* Tokens expiram por `AUTH_TOKEN_EXPIRATION_MINUTES`.
* `AUTH_TOKEN_SECRET` e obrigatorio em producao.
* Rotas administrativas exigem Bearer token.
* `admin`, `analyst` e `viewer` acessam leituras.
* Apenas `admin` e `analyst` podem resolver alertas.
* Login, falha de login, logout e resolucao de alerta registram `audit_logs`.
* `POST /api/v1/agent/checkin` continua separado e protegido por `X-Agent-Api-Key`.

Impactos:

* O dashboard passa a ter tela de login.
* O frontend guarda o token no navegador e o envia para o proxy interno.
* A revogacao server-side antes da expiracao fica fora do escopo atual.
* API Key individual por agente fica planejada para evolucao futura.

---

# ADR-023

## Data

2026-07-28

## Decisao

Isentar as rotas `/api/backend/` do HTTP Basic Auth do Nginx, mantendo o Basic Auth apenas nas paginas e assets servidos por `location /`.

## Motivo

Essas rotas carregam `Authorization: Bearer <token>` da aplicacao apos o login (ADR-021, ADR-022). Como o HTTP permite apenas um cabecalho `Authorization` por requisicao, o Basic Auth aplicado indiscriminadamente quebrava toda chamada autenticada do dashboard (`/me`, `/machines`, `/alerts`, `/security-events`), causando um loop de login. Incidente registrado em `docs/deployment/POSTMORTEMS.md` (INCIDENTE 020).

## Alternativas Avaliadas

* Remover o Basic Auth completamente do Nginx, dependendo apenas do login da aplicacao.
* Fazer o frontend enviar as credenciais de Basic Auth por outro mecanismo alem do cabecalho `Authorization` (ex.: cookie proprio).
* Isentar apenas as rotas de API usadas pela SPA do Basic Auth, mantendo-o nas paginas.

## Resultado

Adicionada `location ^~ /api/backend/` sem `auth_basic` em `infra/nginx/nginx.conf.template`, seguindo o mesmo padrao ja usado por `POST /api/v1/agent/checkin`. As rotas seguem protegidas pelo RBAC/Bearer da propria aplicacao.

Impactos:

* O Basic Auth do Nginx passa a proteger apenas o carregamento inicial das paginas e assets estaticos, nao mais as chamadas de API da SPA.
* A superficie sem Basic Auth aumenta ligeiramente, mas essas rotas ja exigiam autenticacao e RBAC proprios do backend.
* O Basic Auth continua sendo apenas uma camada adicional do MVP; sua real necessidade deve ser reavaliada agora que o login administrativo completo (ADR-021, ADR-022) esta em producao.

---

# ADR-024

## Data

2026-07-28

## Decisao

Adotar Terraform (provider oficial `oci`) para provisionar e versionar a camada de infraestrutura abaixo do sistema operacional do Edge Node (VCN, subnets, security list, instancia de computacao), introduzido via `terraform import` dos recursos ja existentes em producao — nunca destroy/recreate — mantendo os scripts de deploy/backup/restore/rollback em `infra/scripts/` inalterados e fora do escopo do Terraform.

## Motivo

A VM `itcenter-edge-01` roda em producao com dados reais e sua configuracao real (shape, availability domain, regiao, compartment) nunca ficou documentada em nenhum lugar do repositorio. Terraform via import fecha essa lacuna, tornando a infraestrutura auditavel em codigo e revisavel por mudanca, alinhado ao principio ja aplicado aos scripts de deploy e ao bootstrap proposto em `docs/deployment/BOOTSTRAP.md`. Tambem atende ao objetivo declarado do projeto de servir como aprendizado deliberado de Infraestrutura e DevOps.

## Alternativas Avaliadas

* Continuar 100% manual via Console/CLI da Oracle Cloud.
* Documentar apenas em Markdown os parametros da VM, sem nenhuma automacao.
* Usar Pulumi ou CDK for Terraform.
* Usar Ansible tambem para a camada de provisionamento.
* Adotar Terraform com import dos recursos existentes e state local migrando para backend remoto — escolhida.

## Resultado

* Criado `infra/terraform/` com `modules/network`, `modules/compute` e `environments/production`.
* Documentado em `docs/architecture/IAC.md`, no mesmo padrao de `NETWORK.md`/`INFRASTRUCTURE.md`.
* State local na introducao, com migracao planejada para backend remoto em OCI Object Storage.
* Todos os recursos existentes (VCN, subnets, security list, instancia) serao importados sem destruir/recriar nada; `terraform plan` exigido em zero diferenca antes de qualquer apply real.
* `docs/deployment/BOOTSTRAP.md` permanece a fonte de verdade da preparacao do host; o `user_data` do Terraform so referenciara o bootstrap apos os scripts serem implementados e testados fora de producao.
* `.gitignore` atualizado com artefatos de Terraform.
* Trabalho rastreado na EPIC 15 de `docs/development/TASKS.md` e na Fase 12 de `docs/development/ROADMAP.md`.

Impactos:

* Nova tecnologia (Terraform) entra na stack aprovada do projeto.
* Shape, availability domain, regiao e compartment da VM passam a ser descobertos e documentados.
* Mudancas futuras de infraestrutura passam a exigir `terraform plan` revisado antes de qualquer `apply`.

---

# ADR-025

## Data

2026-07-28

## Decisao

Manter o agente Windows em PowerShell (reafirmando o ADR-005). Nao reescrever em Python. Registrar Go como candidata a uma eventual reescrita futura, condicionada a necessidade real de robustez/escala que o hardening incremental em PowerShell nao resolva.

## Motivo

Uma avaliacao do codigo atual (`agent-windows/itcenter-agent.ps1`, `install-agent.ps1`, `uninstall-agent.ps1`) identificou lacunas reais de robustez: chave de API em texto puro no `config.json`, fila de cache offline sem tratamento de arquivo corrompido (um unico arquivo quebrado trava o reenvio de todos os mais novos), sem rotacao de `logs/`/`cache/`, medicao de CPU via `Win32_Processor.LoadPercentage` (conhecida por ser imprecisa), inventario de programas que nao cobre apps UWP/Store, deteccao de USB restrita a armazenamento, ausencia de try/catch no nivel mais alto de `Start-ItCenterAgent`, e scripts nao assinados.

Nenhuma dessas lacunas e causada pela linguagem — sao gaps de implementacao que existiriam igualmente em Python. Trocar de linguagem agora pagaria o custo de reescrever toda a coleta WMI/registro, o instalador e os testes, sem resolver os problemas reais, e iria contra o ADR-005 (PowerShell ja vem em todo Windows; Python exigiria runtime pre-instalado ou um binario PyInstaller de dezenas de MB, o mesmo atrito que o ADR-005 buscava evitar).

Go, ao contrario de Python, resolveria uma limitacao real caso o projeto decida migrar futuramente: compila para um binario nativo estatico sem runtime, mais facil de assinar (Authenticode) e com tipagem forte, mas isso so se justifica se o hardening incremental em PowerShell (EPIC 16) se mostrar insuficiente.

## Alternativas Avaliadas

* Reescrever o agente em Python.
* Reescrever o agente em Go imediatamente.
* Reescrever o agente em C#/.NET.
* Manter PowerShell e corrigir as lacunas concretas incrementalmente, registrando Go como opcao futura condicional — escolhida.

## Resultado

* Agente Windows permanece em PowerShell.
* Lacunas concretas identificadas viram checklist na EPIC 16 (`docs/development/TASKS.md`).
* Avaliacao de reescrita em Go registrada como item condicional na EPIC 14 (Melhorias Futuras), a ser retomada somente se o hardening incremental nao for suficiente.

Impactos:

* Nenhuma mudanca de stack agora; nenhum ADR de linguagem e necessario ate uma decisao futura de fato tomar esse caminho.
* Esforco de curto prazo vai para corrigir os itens concretos de robustez, nao para uma reescrita.

---

# ADR-026

## Data

2026-08-03

## Decisão

Adotar apenas recursos nativos do Claude Code (subagents em `.claude/agents/`, slash commands em `.claude/commands/` e a ferramenta Workflow para pipelines) para orquestrar agentes especializados por domínio (backend, frontend, devops, security, architecture, documentation) neste repositório. Não adotar Strix, OpenAI ou Gemini como providers do fluxo de codificação, e não construir um framework Python próprio de orquestração (`.agent/`, `AgentManager`, abstração de `Provider`).

## Motivo

Um plano externo de "Agent Manager" foi avaliado para dar ao Claude Code acesso a agentes especializados como se fossem Skills nativas. A maior parte do que o plano propunha (roteador de tarefas, biblioteca de prompts por skill, pipeline engine, CLI própria) já existe nativamente no Claude Code via subagents, slash commands e a ferramenta Workflow — construir uma camada Python paralela reimplementaria isso sem necessidade concreta, o que viola a regra de "não adicionar tecnologias sem justificativa" (`docs/development/CONTRIBUTING.md`).

Adicionar OpenAI ou Gemini como providers colocaria código, documentação interna e potencialmente dados operacionais trafegando para APIs de terceiros sem que exista hoje um problema concreto que justifique essa exposição — um risco desproporcional para um produto de segurança (`docs/security/SECURITY.md`) sem nenhum mecanismo de mascaramento de segredos implementado. Strix é um agente de teste de segurança autônomo (pentest); usá-lo como parte do fluxo diário de codificação misturaria um agente com potencial de execução autônoma no próprio ambiente do produto sem um gate de aprovação humana e sem escopo isolado.

## Alternativas Avaliadas

* Implementar o framework Python completo do plano original, com abstração de `Provider` para Strix, Claude, OpenAI e Gemini, roteador customizado em YAML, cache de tarefas e CLI própria.
* Implementar apenas o framework Python (sem os providers externos), reimplementando em Python o que subagents/commands/Workflow já fazem no Claude Code.
* Usar somente subagents, slash commands e a ferramenta Workflow nativos do Claude Code, sem providers externos — escolhida.

## Resultado

* Seis subagents criados em `.claude/agents/`: `backend`, `frontend`, `devops` (inclui responsabilidades de SRE, dado que o projeto roda em uma única VM sem equipe de SRE dedicada), `security`, `architecture` e `documentation`.
* Seis slash commands em `.claude/commands/` (`/backend`, `/frontend`, `/devops`, `/security`, `/architecture`, `/docs`) que delegam ao subagent correspondente.
* Um comando `/feature` que usa a ferramenta Workflow nativa para o pipeline `architecture → implementation → (review + security em paralelo) → docs`.
* Convenção documentada em `docs/development/AI_WORKFLOW.md`.
* Strix, OpenAI, Gemini, cache de tarefas, CLI própria e logging customizado ficam fora de escopo por ora; qualquer um deles exigiria um ADR próprio se uma necessidade concreta e isolada aparecer (ex.: um pentest formal e autorizado via Strix antes de um lançamento público).

Impactos:

* Nenhuma tecnologia nova entra na stack aprovada do projeto (subagents/commands/Workflow são recursos do Claude Code, a ferramenta que já era usada para desenvolver o projeto).
* Nenhum dado do projeto passa a trafegar para APIs de IA de terceiros.
* Mudanças de código e infraestrutura do produto continuam seguindo o fluxo normal de `docs/development/CONTRIBUTING.md`; o que muda é apenas como as tarefas são roteadas para o contexto certo dentro do Claude Code.

---

## ADR-XXX

### Data

YYYY-MM-DD

### Decisão

Descrição da decisão.

### Motivo

Justificativa.

### Alternativas Avaliadas

Lista de alternativas.

### Resultado

Decisão final.
