# IT Center Security Cloud

> Plataforma full stack para monitoramento, inventário, observabilidade e segurança de máquinas Windows, com agente PowerShell, API FastAPI, PostgreSQL, dashboard web e práticas iniciais de SOC/Blue Team.

Status: Fases 0 a 4 concluídas | Ambiente local Docker operacional | Infraestrutura de produção preparada | Publicação na Oracle Cloud pendente.

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
│
├── README.md
├── PROJECT_PLAN.md
├── .gitignore
├── .env.example
├── .env.production.example
│
├── backend/
│   └── app/
│
├── frontend/
│   └── dashboard/
│
├── agent-windows/
│   ├── itcenter-agent.ps1
│   └── config.json
│
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.production.yml
│   ├── nginx/
│   │   └── nginx.conf.template
│   └── scripts/
│
└── docs/
    ├── ARCHITECTURE.md
    ├── DATABASE.md
    ├── API.md
    ├── AGENT.md
    ├── SECURITY.md
    ├── SOC_RULES.md
    ├── ASSET_POLICY.md
    ├── DECISIONS.md
    ├── TASKS.md
    ├── ROADMAP.md
    ├── DEPLOYMENT.md
    └── CONTRIBUTING.md
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

Os detalhes e as limitações conhecidas estão em `docs/SECURITY.md` e `docs/DEPLOYMENT.md`.

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
docs/ASSET_POLICY.md
```

As regras de detecção estarão em:

```text
docs/SOC_RULES.md
```

---

## Deploy

O deploy em produção está preparado, mas ainda não foi publicado na Oracle Cloud.

Ambiente de destino:

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

O ambiente local usa `infra/docker-compose.yml`. Para produção, use `infra/docker-compose.production.yml`, que publica apenas o Nginx nas portas 80 e 443; os demais serviços permanecem na rede interna do Docker. O procedimento completo, incluindo DNS, certificado TLS, credencial administrativa, preflight, backup e renovação de certificado, está em `docs/DEPLOYMENT.md`.

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
| docs/ARCHITECTURE.md | Arquitetura técnica                        |
| docs/DATABASE.md     | Modelagem do banco                         |
| docs/API.md          | Contrato da API                            |
| docs/AGENT.md        | Contrato do agente Windows                 |
| docs/SECURITY.md     | Segurança da aplicação                     |
| docs/SOC_RULES.md    | Regras de detecção SOC                     |
| docs/ASSET_POLICY.md | Política de ativos e softwares autorizados |
| docs/DECISIONS.md    | Registro de decisões arquiteturais         |
| docs/TASKS.md        | Backlog técnico                            |
| docs/ROADMAP.md      | Evolução do produto                        |
| docs/DEPLOYMENT.md   | Estratégia de deploy                       |
| docs/CONTRIBUTING.md | Guia de contribuição                       |

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

### Fase 5 - Deploy Cloud — pendente de publicação

* Oracle Cloud
* Docker Compose
* Nginx
* HTTPS

### Fase 6 - Governança

* Login
* Perfis e controle de acesso
* Auditoria

### Fase 7 - SOC Avançado

* Wazuh
* OpenVAS

### Fase 8 - SaaS

* Multiempresa
* Multiusuário
* SaaS

---

## Autor

Desenvolvido por Daniel da Silva Azevedo como projeto de portfólio e aprendizado prático em Infraestrutura, DevOps, Cloud, Observabilidade e Cyber Security.
