# IT Center Security Cloud

> Plataforma full stack para monitoramento, inventário, observabilidade e segurança de máquinas Windows, com agente PowerShell, API FastAPI, PostgreSQL, dashboard web e práticas iniciais de SOC/Blue Team.

Status resumido: Fases 0 a 9 concluídas (governança/autenticação e operação/segurança de produção validadas em produção real) | Fase 12 (Terraform/IaC) quase concluída — 4 pendências de infraestrutura | Fases 13 a 17 concluídas (hardening do agente Windows, incluindo assinatura de código; hardening do dashboard; orquestração de agentes de IA; hub de integração RustDesk — Snipe-IT foi implementado e revertido, ver ADR-033; relatórios/dashboard executivo) | Fase 18 (observabilidade de infraestrutura) e Fase 19 (auto-atualização do agente) com planejamento e ADRs concluídos, implementação pendente | Ambiente local Docker operacional | Produção publicada na Oracle Cloud | Agente Windows integrado ao check-in. Progresso detalhado por EPIC está em `docs/development/TASKS.md` (backlog oficial, sempre atualizado); fases, matriz de rastreabilidade e ADRs relacionados estão em `docs/development/ROADMAP.md`.

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

O IT Center Security Cloud é uma plataforma criada para monitorar computadores e servidores Windows por meio de agentes leves, centralizando informações de inventário, desempenho e segurança em um dashboard web e permitindo maior visibilidade sobre ativos corporativos.

A visão completa do produto — problema resolvido, público-alvo, princípios, escopo do MVP e visão de longo prazo — está em `PROJECT_PLAN.md`.

---

## Objetivo

Cadastrar máquinas automaticamente, coletar métricas de CPU/RAM/disco, registrar inventário básico, monitorar status online/offline, detectar eventos de segurança e gerar alertas iniciais de SOC, hospedando tudo em ambiente gratuito.

Objetivos detalhados (principal, técnicos, profissionais) e indicadores de sucesso do MVP estão em `PROJECT_PLAN.md`.

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
| --------------- | ----------------------------------------------------------- |
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

Stack oficial (backend, frontend, banco, agente e infraestrutura) e as regras para adotar tecnologia nova estão documentadas em `docs/development/CONTRIBUTING.md` (seções "Stack Oficial" e "Tecnologias Não Permitidas no MVP").

Resumo: Python/FastAPI + PostgreSQL no backend, Next.js/TypeScript no frontend, PowerShell no agente Windows, Docker Compose + Nginx + Terraform (somente VCN, subnets, security list e instância — ADR-024) na infraestrutura, hospedado na Oracle Cloud Free Tier.

---

## Estrutura do Projeto

```text
it-center-security-cloud/
|-- README.md
|-- PROJECT_PLAN.md
|-- .claude/
|   |-- agents/
|   `-- commands/
|-- backend/
|   `-- app/
|-- frontend/
|   `-- dashboard/
|-- agent-windows/
|-- infra/
|   |-- docker-compose.yml
|   |-- docker-compose.production.yml
|   |-- nginx/
|   |-- scripts/
|   `-- terraform/
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

Publicado na Oracle Cloud (`itcenter-daniel.chickenkiller.com`, IP `147.15.78.220`, VM `itcenter-edge-01`, Ubuntu Server 24.04), atrás de Nginx como único ponto de entrada público (portas 80/443); frontend, backend e PostgreSQL permanecem na rede interna do Docker.

O guia completo de operação — setup, produção, validação, backup, rollback, renovação de TLS e troubleshooting — está em `docs/README.md` e `docs/deployment/PRODUCTION.md`. Índice de todos os guias de deployment: `docs/README.md`.

Comando principal de produção na VM:

```bash
cd /opt/itcenter/app/it-center-security-cloud
sh infra/scripts/deploy.sh
```

O agente Windows já está integrado ao ambiente publicado: check-in via `POST /api/v1/agent/checkin`, autenticado por `X-Agent-Api-Key`. Contrato e troubleshooting do agente em `docs/agent/CHECKIN.md` e `docs/agent/TROUBLESHOOTING.md`.

---

## Como Executar

O guia completo (local e produção, com todos os comandos de validação) está em `docs/README.md`.

Fluxo local resumido:

```bash
git clone <repo-url>
cd it-center-security-cloud
cp .env.example .env
docker compose -f infra/docker-compose.yml up --build
```

URLs locais: Dashboard `http://127.0.0.1:3000` · Backend `http://127.0.0.1:8000/api/v1/health` · Postgres `127.0.0.1:5432`

Parar: `docker compose -f infra/docker-compose.yml down` (adicione `-v` para também apagar os dados locais do banco).

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

Visão resumida por fase. Entregas detalhadas, critérios de conclusão e o status atualizado de cada EPIC estão em `docs/development/TASKS.md` (backlog oficial, sempre atualizado — fonte de verdade sobre progresso); fases, matriz de rastreabilidade e ADRs relacionados estão em `docs/development/ROADMAP.md`.

| Fase | Tema | Status |
| --- | --- | --- |
| 0-9 | Planejamento; backend, agente e dashboard MVP; SOC Light; deploy cloud; agente em produção; validação fim a fim; governança/autenticação; operação e segurança de produção | Concluídas |
| 10 | SOC Avançado (Wazuh, OpenVAS) | Não iniciada |
| 11 | SaaS (multiempresa, multiusuário, billing) | Não iniciada |
| 12 | Infraestrutura como Código (Terraform, ADR-024) | Quase concluída — 4 pendências de infraestrutura (bucket OCI e migração de state remoto, scripts de bootstrap, variável de cloud-init) |
| 13 | Hardening do Agente Windows, incluindo assinatura de código (ADR-025, ADR-031) | Concluída |
| 14 | Hardening do Dashboard (Frontend) | Concluída |
| 15 | Orquestração de Agentes de IA (ADR-026) | Concluída |
| 16 | Hub de Integração: RustDesk (ADR-027). Snipe-IT (ADR-028) implementado e revertido, ver ADR-033 | Concluída |
| 17 | Relatórios PDF e Dashboard Executivo (ADR-029) | Concluída |
| 18 | Observabilidade de Infraestrutura — Prometheus + Grafana (ADR-030) | Planejamento concluído, implementação pendente |
| 19 | Auto-atualização do Agente Windows (ADR-032) | Planejamento concluído, implementação pendente |

---

## Autor

Desenvolvido por Daniel da Silva Azevedo como projeto de portfólio e aprendizado prático em Infraestrutura, DevOps, Cloud, Observabilidade e Cyber Security.
