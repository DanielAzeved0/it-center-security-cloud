# IT Center Security Cloud

> Plataforma full stack para monitoramento, inventário, observabilidade e segurança de máquinas Windows, com agente PowerShell, API FastAPI, PostgreSQL, dashboard web e práticas iniciais de SOC/Blue Team.

Status: Fases 0 a 5 concluídas | Ambiente local Docker operacional | Produção publicada na Oracle Cloud | Agente Windows integrado ao check-in.

---

## Índice

* Sobre o Projeto
* Objetivo
* Arquitetura
* Fluxo do Sistema
* Funcionalidades Planejadas
* Stack
* Estrutura do Projeto
* Segurança
* SOC Light
* Deploy
* Como Executar
* Documentação
* Roadmap
* Autor

---

## Sobre o Projeto

O IT Center Security Cloud é uma plataforma criada para monitorar computadores e servidores Windows por meio de agentes leves.

A proposta é centralizar informações de inventário, desempenho e segurança em um dashboard web, permitindo maior visibilidade sobre ativos corporativos.

O projeto nasceu com foco em:

* Infraestrutura de TI
* Monitoramento
* Inventário
* Observabilidade
* Segurança defensiva
* SOC Light
* DevOps
* Cloud gratuita

---

## Objetivo

Criar uma solução simples, gratuita e escalável para:

* Cadastrar máquinas automaticamente.
* Coletar métricas de CPU, RAM e disco.
* Registrar inventário básico.
* Monitorar status online/offline.
* Detectar eventos de segurança.
* Gerar alertas iniciais de SOC.
* Hospedar tudo em ambiente gratuito.

---

## Arquitetura

```text
Internet
      ↓
Oracle Cloud VCN (10.0.0.0/16)
      ↓
Subnet pública (10.0.0.0/24)
      ↓
itcenter-edge-01 (Ubuntu Server 24.04)
      ↓
Nginx → Next.js → FastAPI → PostgreSQL
```

| Camada          | Responsabilidade                                          |
| --------------- | --------------------------------------------------------- |
| Agente Windows  | Coleta inventário, métricas e eventos de segurança        |
| Backend FastAPI | Recebe check-ins, processa dados e expõe endpoints        |
| PostgreSQL      | Armazena máquinas, métricas, programas, eventos e alertas |
| Dashboard Web   | Exibe máquinas, métricas, inventário e alertas            |
| Nginx           | Proxy reverso, HTTPS e exposição segura                   |
| Docker Compose  | Orquestra os containers do MVP                            |

No MVP, todos os containers de produção executam no nó de borda `itcenter-edge-01`. Somente o Nginx recebe tráfego público nas portas 80 e 443; frontend, backend e banco permanecem na rede interna do Docker. A subnet privada `10.0.1.0/24` fica reservada para a futura separação dos serviços, sem alterar a entrada pública do sistema.

---

## Fluxo do Sistema

```text
1. O agente PowerShell roda na máquina Windows.
2. Ele coleta hostname, usuário, IP, CPU, RAM, disco e dados de segurança.
3. Os dados são enviados para a API.
4. A API salva as informações no PostgreSQL.
5. O dashboard consulta a API.
6. O usuário visualiza máquinas, métricas e alertas.
```

---

## Funcionalidades Planejadas

### Inventário

* Hostname
* Usuário logado
* IP
* Sistema operacional
* Versão do Windows
* Programas instalados

### Monitoramento

* CPU
* RAM
* Disco
* Uptime
* Último check-in
* Status online/offline

### Segurança

* Firewall
* Windows Defender
* RDP
* Usuários administradores locais
* Dispositivos USB
* Ferramentas de acesso remoto

### SOC Light

* Falhas de login
* Novo administrador local
* Firewall desativado
* Defender desativado
* RDP habilitado sem autorização
* Software remoto não autorizado
* Torrent detectado
* Máquina desconhecida

---

## Stack

| Camada           | Tecnologia             |
| ---------------- | ---------------------- |
| Backend          | Python, FastAPI        |
| Banco de Dados   | PostgreSQL             |
| Frontend         | Next.js, TypeScript    |
| Agente           | PowerShell             |
| Infraestrutura   | Docker, Docker Compose |
| Proxy            | Nginx                  |
| Hospedagem       | Oracle Cloud Free Tier |
| Segurança futura | Wazuh, OpenVAS         |

---

## Estrutura do Projeto

```text
it-center-security-cloud/
|-- README.md
|-- PROJECT_PLAN.md
|-- backend/
|   `-- app/
|-- frontend/
|   `-- dashboard/
|-- agent-windows/
|-- infra/
|   |-- docker-compose.yml
|   |-- docker-compose.production.yml
|   |-- nginx/
|   `-- scripts/
`-- docs/
    |-- README.md
    |-- architecture/
    |-- deployment/
    |-- security/
    |-- backend/
    |-- agent/
    |-- development/
    `-- assets/
```

---

## Segurança

O projeto aplica os seguintes controles de segurança:

* Não coletar senhas.
* Não coletar histórico de navegação.
* Não coletar conteúdo de arquivos pessoais.
* Não armazenar secrets no GitHub.
* Utilizar `.env` e `.env.production` para variáveis sensíveis, sem versionar segredos.
* Exigir `X-Agent-Api-Key` no check-in do agente.
* Validar payloads recebidos dos agentes.
* Utilizar HTTPS obrigatório em produção.
* Manter PostgreSQL, FastAPI e Next.js sem portas públicas em produção.
* Proteger o dashboard e a proxy administrativa com HTTP Basic no Nginx.
* Executar o preflight de produção e a verificação de CVEs antes da publicação.

Os detalhes e as limitações conhecidas estão em `docs/security/SECURITY.md` e `docs/deployment/PRODUCTION.md`.

---

## SOC Light

O projeto terá uma camada inicial de práticas SOC/Blue Team.

As regras serão baseadas em contexto e política de ativos.

Exemplo:

```text
RustDesk instalado em máquina autorizada:
    registrar evento

RustDesk instalado em máquina não autorizada:
    gerar alerta

Torrent detectado:
    gerar alerta imediato
```

A fonte de verdade para softwares autorizados será:

```text
docs/security/ASSET_POLICY.md
```

As regras de detecção estarão em:

```text
docs/security/SOC_RULES.md
```

---

## Deploy

O deploy em produção está publicado na Oracle Cloud e foi validado pelo workflow manual `Deploy Production` do GitHub Actions.

Ambiente atual:

```text
Oracle Cloud Free Tier
VCN: 10.0.0.0/16
Subnet pública: 10.0.0.0/24
Subnet privada reservada: 10.0.1.0/24
itcenter-edge-01: Ubuntu Server 24.04
Docker
Docker Compose
Nginx
PostgreSQL
FastAPI
Next.js
```

Objetivo:

Manter o MVP com custo zero.

O ambiente local usa `infra/docker-compose.yml`. Para produção, a proposta de bootstrap versionado do Edge Node está documentada em `docs/deployment/BOOTSTRAP.md`. A publicação usa `infra/scripts/deploy.sh` e `infra/docker-compose.production.yml`, que publica apenas o Nginx nas portas 80 e 443; os demais serviços permanecem na rede interna do Docker. O procedimento completo, incluindo DNS, certificado TLS, credencial administrativa, preflight, backup, rollback e renovação de certificado, está em `docs/deployment/PRODUCTION.md`.

Comando principal de producao na VM:

```bash
cd /opt/itcenter/app/it-center-security-cloud
sh infra/scripts/deploy.sh
```

### Producao atual

```text
Dominio: itcenter-daniel.chickenkiller.com
IP publico: 147.15.78.220
VM: Oracle Cloud Ubuntu 24.04 LTS
Rede Docker: itcenter-network
Entrada publica: Nginx 80/443
```

Fluxo de comunicacao:

```mermaid
flowchart TD
    agent[Windows Agent] -->|HTTPS + X-Agent-Api-Key| nginx[Nginx]
    browser[Browser] -->|HTTPS + Basic Auth| nginx
    nginx --> frontend[Next.js Dashboard]
    nginx --> backend[FastAPI Backend]
    frontend --> backend
    backend --> postgres[PostgreSQL]
```

Somente o Nginx expoe portas publicas. PostgreSQL, FastAPI e Next.js permanecem internos na rede Docker.

### Guias de producao

| Guia | Finalidade |
| --- | --- |
| `docs/deployment/ORACLE_CLOUD.md` | Implantacao completa na Oracle Cloud. |
| `docs/deployment/SETUP.md` | Preparacao do ambiente de producao. |
| `docs/deployment/HTTPS.md` | DNS, Certbot, TLS e renovacao. |
| `docs/deployment/DEPLOYMENT_HISTORY.md` | Historico real da implantacao feita. |
| `docs/deployment/TROUBLESHOOTING.md` | Diagnostico operacional. |
| `docs/deployment/KNOWN_ISSUES.md` | Limitacoes e problemas conhecidos. |
| `docs/deployment/LESSONS_LEARNED.md` | Aprendizados da implantacao. |
| `docs/architecture/INFRASTRUCTURE.md` | Arquitetura de infraestrutura. |
| `docs/architecture/NETWORK.md` | Rede, DNS e portas. |
| `docs/architecture/CONTAINERS.md` | Containers e responsabilidades. |
| `docs/architecture/SECURITY.md` | Controles de seguranca. |

### Validar ambiente

Na VM:

```bash
cd /opt/itcenter/app/it-center-security-cloud
sh infra/scripts/preflight-production.sh
docker ps
docker compose --env-file .env.production -f infra/docker-compose.production.yml ps
```

Testes principais:

```bash
curl -I https://itcenter-daniel.chickenkiller.com
curl --user admin:SENHA_FORTE_AQUI https://itcenter-daniel.chickenkiller.com
```

### Backup

```bash
cd /opt/itcenter/app/it-center-security-cloud
sh infra/scripts/backup.sh
```

Destino:

```text
/opt/itcenter/backups
```

### HTTPS e dominio

O dominio atual e:

```text
itcenter-daniel.chickenkiller.com
```

Certificados esperados:

```text
/etc/letsencrypt/live/itcenter-daniel.chickenkiller.com/fullchain.pem
/etc/letsencrypt/live/itcenter-daniel.chickenkiller.com/privkey.pem
```

Se um provedor local nao resolver o dominio, valide com resolvers publicos:

```bash
dig @8.8.8.8 itcenter-daniel.chickenkiller.com
dig @1.1.1.1 itcenter-daniel.chickenkiller.com
dig @9.9.9.9 itcenter-daniel.chickenkiller.com
```

### Agente Windows

O agente Windows ja esta integrado ao ambiente publicado. O check-in de producao usa `POST /api/v1/agent/checkin` via HTTPS e autentica com o header `X-Agent-Api-Key`, que deve ser igual ao `AGENT_API_KEY` definido na VM.

Proximas evolucoes do agente:

* Separar o agente como produto independente.
* Criar instalador.
* Criar servico Windows.
* Adicionar atualizacao automatica.
* Expandir inventario, metricas e eventos de seguranca.
* Adicionar cache offline, retry inteligente, compressao, criptografia e assinatura de payloads.

### Troubleshooting rapido

```bash
docker logs itcenter-nginx
docker logs itcenter-frontend
docker logs itcenter-backend
docker logs itcenter-postgres
```

Guias detalhados:

```text
docs/deployment/TROUBLESHOOTING.md
docs/deployment/KNOWN_ISSUES.md
docs/deployment/LESSONS_LEARNED.md
```

---

## Como Executar

Fluxo local recomendado:

```bash
git clone <repo-url>
cd it-center-security-cloud
cp .env.example .env
docker compose -f infra/docker-compose.yml up --build
```

No Windows, se o terminal estiver em `C:\Users\Famili Azevedo`, entre na raiz do projeto antes:

```powershell
cd "C:\Users\Famili Azevedo\Desktop\it-center-security-cloud"
docker compose -f infra/docker-compose.yml up --build
```

Em segundo plano:

```bash
docker compose -f infra/docker-compose.yml up --build -d
```

Servicos iniciados:

```text
postgres
backend
frontend
```

URLs locais:

```text
Dashboard: http://127.0.0.1:3000
Backend:   http://127.0.0.1:8000/api/v1/health
Postgres:  127.0.0.1:5432
```

Parar:

```bash
docker compose -f infra/docker-compose.yml down
```

Parar e apagar dados locais do banco:

```bash
docker compose -f infra/docker-compose.yml down -v
```

---

## Documentação

| Arquivo              | Função                                     |
| -------------------- | ------------------------------------------ |
| PROJECT_PLAN.md      | Visão estratégica do projeto               |
| docs/README.md       | Índice global da documentação              |
| docs/architecture/   | Arquitetura e fluxo de dados               |
| docs/deployment/     | Setup, produção e troubleshooting          |
| docs/security/       | Segurança, autenticação e regras SOC       |
| docs/backend/        | API e banco de dados                       |
| docs/agent/          | Agente Windows e check-in                  |
| docs/development/    | Contribuição, roadmap, decisões e tarefas  |
| docs/assets/         | Diagramas e imagens                        |

---

## Roadmap

### Fase 0 - Planejamento — concluída

* Documentação base
* Arquitetura
* Banco
* API
* Agente
* Segurança
* Regras SOC

### Fase 1 - Backend MVP — concluída

* FastAPI
* Health check
* Endpoint de check-in
* PostgreSQL

### Fase 2 - Agente Windows — concluída

* Coleta de inventário
* Coleta de métricas
* Envio para API

### Fase 3 - Dashboard — concluída

* Máquinas online/offline
* Último check-in
* CPU/RAM/Disco

### Fase 4 - SOC Light — concluída

* Eventos de segurança
* Alertas básicos
* Políticas de ativos

### Fase 5 - Deploy Cloud — concluída

* Oracle Cloud
* Bootstrap versionado do Edge Node
* Docker Compose
* Nginx
* HTTPS

### Fase 6 - Agente Windows em Produção

* Instalação controlada
* Tarefa Agendada do Windows
* Configuração de produção
* Logs e cache padronizados
* Check-in real em produção

### Fase 7 - Validação Fim a Fim e Dashboard Operacional

* Fluxo Windows Agent -> Nginx -> FastAPI -> PostgreSQL -> Dashboard
* Detalhes da máquina
* Histórico de métricas
* Eventos por máquina
* Filtros operacionais

### Fase 8 - Governança

* Login
* Perfis e controle de acesso
* Auditoria

### Fase 9 - Operação e Segurança de Produção

* Backup automático
* Restore testado
* Rollback validado
* Monitoramento básico da VM
* Gate de imagens Docker

### Fase 10 - SOC Avançado

* Wazuh
* OpenVAS

### Fase 11 - SaaS

* Multiempresa
* Multiusuário
* SaaS

---

## Autor

Desenvolvido por Daniel da Silva Azevedo como projeto de portfólio e aprendizado prático em Infraestrutura, DevOps, Cloud, Observabilidade e Cyber Security.
