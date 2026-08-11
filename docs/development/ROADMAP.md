# ROADMAP.md

# Roadmap Oficial

## Objetivo

Guiar a evolução do IT Center Security Cloud.

---

## Correspondência Fase ↔ EPIC

Este documento numera as fases detalhadas abaixo como "Fase N" (a partir de 0). O backlog oficial (`docs/development/TASKS.md`) numera o mesmo trabalho como "EPIC N" (a partir de 1). Os números não coincidem — esta tabela traduz um para o outro e existe justamente para evitar o desalinhamento que já ocorreu entre esta numeração e a de TASKS.md:

| Fase | EPIC(s) correspondente(s) |
| --- | --- |
| Fase 0 | EPIC 1 |
| Fase 1 | EPIC 2 e EPIC 3 |
| Fase 2 | EPIC 4 |
| Fase 3 | EPIC 5 |
| Fase 4 | EPIC 6 |
| Fase 5 | EPIC 7 |
| Fase 6 | EPIC 8 |
| Fase 7 | EPIC 9, EPIC 10 e EPIC 11 |
| Fase 8 | EPIC 12 |
| Fase 9 | EPIC 13 |
| Fase 10 | sem EPIC dedicado ainda (parte de EPIC 14 - Melhorias Futuras) |
| Fase 11 | sem EPIC dedicado ainda (parte de EPIC 14 - Melhorias Futuras) |
| Fase 12 | EPIC 15 |
| Fase 13 | EPIC 16 |
| Fase 14 | EPIC 17 |
| Fase 15 | EPIC 18 |
| Fase 16 | EPIC 19 |
| Fase 17 | EPIC 20 |
| Fase 18 | EPIC 21 |
| Fase 19 | EPIC 22 |

---

# Matriz de Rastreabilidade

Esta seção liga o planejamento oficial às tarefas do backlog.

## Planejamento de Produto

`docs/development/ROADMAP.md` e `docs/development/TASKS.md`

```text
EPIC 1 - Fundação do Projeto
EPIC 2 - Backend
EPIC 3 - Banco
EPIC 4 - Agente Windows
EPIC 5 - Dashboard
EPIC 6 - SOC Light
EPIC 7 - Produção
EPIC 8 - Agente Windows em Produção
EPIC 9 - Validação do Fluxo Fim a Fim
EPIC 10 - Dashboard Operacional
EPIC 11 - SOC Light Pendências
EPIC 12 - Governança e Autenticação
EPIC 13 - Operação e Segurança de Produção
EPIC 14 - Melhorias Futuras
EPIC 15 - Infraestrutura como Codigo (Terraform)
EPIC 16 - Hardening do Agente Windows
EPIC 17 - Hardening do Dashboard (Frontend)
EPIC 18 - Orquestracao de Agentes de IA (Claude Code nativo)
EPIC 19 - Hub de Integracao: RustDesk e Snipe-IT
EPIC 20 - Relatorios PDF e Dashboard Executivo
EPIC 21 - Observabilidade de Infraestrutura (Prometheus + Grafana)
EPIC 22 - Auto-atualizacao do Agente Windows (Updater Dedicado)
```

## Arquitetura

`docs/architecture/ARCHITECTURE.md`

```text
Inventário do agente -> EPIC 4
Persistência API/PostgreSQL -> EPIC 2 e EPIC 3
Endpoints do backend -> EPIC 2
Estrutura do dashboard -> EPIC 5
Deploy e containers -> EPIC 7
Agente instalavel -> EPIC 8
Fluxo fim a fim -> EPIC 9
Dashboard operacional -> EPIC 10
Governanca e autenticacao -> EPIC 12
Operacao de producao -> EPIC 13
```

## Banco

`docs/backend/DATABASE.md`

```text
machines -> EPIC 3
metrics -> EPIC 3
installed_programs -> EPIC 3
security_events -> EPIC 3
alerts -> EPIC 3
agent_configs -> EPIC 3
machine_local_admins -> EPIC 6
```

## API

`docs/backend/API.md`

```text
POST /api/v1/agent/checkin -> EPIC 2 e EPIC 4
GET /api/v1/machines/{id} -> EPIC 2
GET /api/v1/machines/{id}/metrics -> EPIC 2
GET /api/v1/machines/{id}/programs -> EPIC 2
PATCH /api/v1/alerts/{id}/resolve -> EPIC 2
```

## Agente

`docs/agent/CHECKIN.md`

```text
Hostname -> EPIC 4
Usuário em execução -> EPIC 4
IP -> EPIC 4
Sistema operacional -> EPIC 4
Programas instalados -> EPIC 4
CPU, RAM e disco -> EPIC 4
Uptime -> EPIC 4
JSON de check-in -> EPIC 4
Envio para API -> EPIC 4
Cache offline e reenvio -> EPIC 4
Instalacao como produto -> EPIC 8
Servico Windows ou tarefa agendada -> EPIC 8
Retry inteligente -> EPIC 8
Validacao contra producao -> EPIC 8 e EPIC 9
```

## SOC Light

`docs/security/SOC_RULES.md`

```text
Firewall, Defender e RDP -> EPIC 6
USB e falhas de login -> EPIC 6
Administradores locais -> EPIC 6
Ferramentas remotas, VPN e torrent -> EPIC 6
Eventos e alertas -> EPIC 6
unknown_asset -> EPIC 11
machine_offline -> EPIC 11
Politicas autorizadas -> EPIC 11
```

## Decisões

`docs/development/DECISIONS.md`

```text
ADR-013 -> mantém a integração direta FastAPI + PostgreSQL
ADR-014 -> padroniza execução local integrada com Docker Compose
ADR-015 -> padroniza gate de seguranca das imagens Docker
ADR-026 -> orquestracao de agentes de IA com recursos nativos do Claude Code
ADR-027 -> RustDesk como acesso remoto integrado (EPIC 19)
ADR-028 -> integracao com Snipe-IT como fonte de ITAM (EPIC 19)
ADR-029 -> ReportLab para relatorios PDF e dashboard executivo (EPIC 20)
ADR-030 -> Prometheus + Grafana para observabilidade de infraestrutura (EPIC 21)
ADR-031 -> certificado self-signed + ExecutionPolicy AllSigned para assinatura de codigo do agente Windows (EPIC 16)
ADR-032 -> updater dedicado (Tarefa Agendada propria) para auto-atualizacao do agente Windows (EPIC 22)
```

---

# Fase 0

Planejamento

Status:

Concluído

Entregas:

* Arquitetura
* Banco
* API
* Segurança
* Regras SOC
* Políticas

---

# Fase 1

MVP Backend

Meta:

Receber dados do agente.

Entregas:

* FastAPI
* PostgreSQL
* Endpoint Health
* Endpoint Check-in

Resultado Esperado:

Máquinas registradas no banco.

---

# Fase 2

Agente Windows

Meta:

Enviar informações da máquina.

Entregas:

* Inventário
* Métricas
* JSON
* Comunicação HTTPS

Resultado Esperado:

Check-in automático.

---

# Fase 3

Dashboard

Meta:

Visualizar máquinas.

Entregas:

* Lista de máquinas
* CPU
* RAM
* Disco
* Online/Offline

Resultado Esperado:

Visibilidade operacional.

---

# Fase 4

SOC Light

Meta:

Adicionar segurança.

Entregas:

* Eventos
* Alertas
* Firewall
* Defender
* USB
* RDP
* Administradores locais
* Ferramentas remotas
* VPNs nao autorizadas
* Torrent

Resultado Esperado:

Primeiros recursos SOC.

Status:

Concluído.

---

# Fase 5

Deploy Cloud

Meta:

Sistema disponível externamente.

Entregas:

* Oracle Cloud
* Bootstrap versionado do Edge Node
* HTTPS
* Docker

Resultado Esperado:

Primeira versão pública.

Status:

Concluído.

---

# Fase 6

Agente Windows em Producao

Meta:

Transformar o agente em componente instalavel e validado contra o ambiente publicado.

Entregas:

* Instalacao controlada
* Servico Windows ou tarefa agendada
* Configuracao de producao
* Logs e cache padronizados
* Retry inteligente
* Primeiro check-in real em producao

Resultado Esperado:

Maquinas Windows enviando dados reais para o dashboard publicado.

---

# Fase 7

Validacao Fim a Fim e Dashboard Operacional

Meta:

Provar o fluxo completo e transformar o dashboard em ferramenta de operacao diaria.

Entregas:

* Evidencia do fluxo Windows Agent -> Nginx -> FastAPI -> PostgreSQL -> Dashboard
* Tela de detalhes da maquina
* Historico de metricas
* Programas instalados por maquina
* Eventos por maquina
* Resolucao de alertas pela interface
* Filtros operacionais

Resultado Esperado:

Operacao diaria baseada em dados reais.

---

# Fase 8

Governanca e Autenticacao

Meta:

Substituir controles minimos do MVP por autenticacao e governanca administrativa.

Entregas:

* Login
* Sessoes ou JWT
* Perfis
* Auditoria
* Planejamento de API Key por agente

Resultado Esperado:

Controle administrativo.

---

# Fase 9

Operacao e Seguranca de Producao

Meta:

Reduzir risco operacional e preparar manutencao continua.

Entregas:

* Backup automatico
* Restore testado
* Rollback validado
* Renovacao TLS validada
* Monitoramento basico da VM
* Gate de imagens Docker

Resultado Esperado:

Ambiente publicado mais confiavel e auditavel.

---

# Fase 10

SOC Avancado

Meta:

Evoluir para Blue Team.

Entregas:

* Wazuh
* OpenVAS
* IOC Detection
* Correlacao
* MITRE ATT&CK

Resultado Esperado:

SOC corporativo.

---

# Fase 11

SaaS

Meta:

Transformar em produto.

Entregas:

* Multiempresa
* Multiusuario
* Billing
* Gestao de clientes

Resultado Esperado:

Produto comercializável.

---

# Fase 12

Infraestrutura como Codigo — quase concluida (ADR-024), 4 pendencias de infraestrutura

Meta:

Provisionar e versionar via Terraform a camada de infraestrutura Oracle Cloud sem destruir o ambiente de producao existente.

Entregas:

* Modulos Terraform (network e compute)
* Import dos recursos existentes, com `terraform plan` em "No changes." (concluido em 2026-08-04)
* Documentacao de shape, availability domain, regiao e compartment antes ausente (concluido)

Pendente (4 itens; detalhes e progresso em EPIC 15 de `docs/development/TASKS.md`):

* Bucket OCI Object Storage para state remoto
* Migracao do state para o backend remoto (`terraform init -migrate-state`)
* Scripts de bootstrap (`infra/bootstrap/{01-system,02-packages,03-directories,04-docker,05-firewall,bootstrap}.sh`) conforme `docs/deployment/BOOTSTRAP.md`
* Variavel opcional de cloud-init/bootstrap no module compute (sem ativar em producao)

Resultado Esperado:

Infraestrutura reproduzivel e auditavel em codigo, sem alterar o fluxo de deploy da aplicacao existente.

---

# Fase 13

Hardening do Agente Windows — concluida (ADR-025, ADR-031)

Meta:

Corrigir lacunas concretas de robustez identificadas no agente PowerShell (ADR-025), sem trocar de linguagem.

Entregas:

* ACL restrita em config.json para proteger o agent_api_key em texto puro
* Quarentena para arquivo de cache corrompido
* Retencao/limite de idade para cache e rotacao de logs
* Medicao de CPU mais precisa
* Inventario cobrindo apps UWP/Store
* Deteccao de USB alem de armazenamento
* Tratamento de erro no nivel mais alto do agente
* Scripts assinados com certificado Authenticode self-signed e ExecutionPolicy `AllSigned` (ADR-031; `RemoteSigned` foi descartado por nao verificar scripts sobrescritos localmente, o vetor de ataque real) — implementado no commit `969201b`

Resultado Esperado:

Agente Windows mais resiliente e auditavel, mantendo PowerShell como linguagem oficial.

---

# Fase 14

Hardening do Dashboard (Frontend) — concluida

Meta:

Corrigir os riscos identificados na auditoria de seguranca do frontend de 2026-07-29 (token de sessao em localStorage, ausencia de security headers, falta de middleware de sessao, fallback de env var no proxy interno, auditoria de dependencias bloqueada), mantendo Next.js/React como stack oficial.

Entregas:

* Token de sessao migrado para cookie httpOnly + Secure (condicional a HTTPS real) + SameSite=Strict, setado e lido pelo proxy `/api/backend`
* `Content-Security-Policy` configurada em `next.config.mjs`; `X-Frame-Options`, `X-Content-Type-Options` e `Referrer-Policy` deliberadamente nao duplicados (ja aplicados pelo Nginx em producao)
* `middleware.ts` com gate de sessao no edge (checagem de presenca do cookie)
* Fallback `NEXT_PUBLIC_API_BASE_URL` removido do proxy interno; allowlist explicita de rotas adicionada
* Rotina de auditoria de dependencias do frontend (`npm audit --audit-level=high`) restabelecida via CI, fora do proxy corporativo local
* Confirmado que mensagens de erro (`detail`) do backend nao vazam detalhes internos

Resultado Esperado:

Dashboard com superficie de ataque client-side reduzida e defesa em profundidade equivalente ao restante da plataforma, sem trocar a stack atual.

---

# Fase 15

Orquestracao de Agentes de IA — concluida

Meta:

Configurar o Claude Code para atuar como especialistas de dominio (backend, frontend, devops, security, architecture, documentation) usando apenas recursos nativos, em vez de um framework Python proprio com multiplos providers externos (ADR-026).

Entregas:

* Subagents em `.claude/agents/` (backend, frontend, devops, security, architecture, documentation)
* Slash commands em `.claude/commands/` que delegam a cada subagent
* Pipeline `/feature` via Workflow tool nativa (architecture -> implementation -> review + security -> docs)
* `docs/development/AI_WORKFLOW.md` documentando a convencao e o que foi deliberadamente descartado (Strix, OpenAI, Gemini, cache de tarefas, CLI propria)

Resultado Esperado:

Especialistas de dominio dentro do Claude Code sem nenhuma tecnologia nova na stack e sem dado do projeto trafegando para APIs de IA de terceiros.

---

# Fase 16

Hub de Integracao: RustDesk e Snipe-IT — concluida (ADR-027, ADR-028)

Meta:

Entregar as duas integracoes do Hub (Fase H de `docs/architecture/FUTURE_ARCHITECTURE.md`) priorizadas em 2026-08-03 por menor esforco e maior valor imediato: RustDesk (acesso remoto) e Snipe-IT (ITAM).

Entregas:

* RustDesk: coluna `machines.rustdesk_id`, endpoint `PATCH /api/v1/machines/{id}/rustdesk`, botao "Conectar" no detalhe da maquina, RBAC restrito a admin/analyst.
* Snipe-IT: servico de integracao desacoplado, secrets `SNIPEIT_BASE_URL`/`SNIPEIT_API_TOKEN`, coluna `machines.snipeit_asset_id`, sincronizacao automatica no check-in, link "Ver no Snipe-IT" no dashboard.

Resultado Esperado:

Acesso remoto e inventario administrativo integrados ao dashboard sem o IT Center reimplementar nenhuma das duas especialidades.

Validado em 2026-08-11: suite completa do backend com 87 testes passando (`pytest`, PostgreSQL local via Docker Compose), incluindo os testes dedicados de RustDesk e Snipe-IT. EPIC 19 encerrada.

---

# Fase 17

Relatorios PDF e Dashboard Executivo — concluida (ADR-029)

Meta:

Entregar exportacao de relatorios em PDF e uma visao executiva resumida do dashboard.

Entregas:

* Biblioteca `reportlab` no backend (compativel com a base Alpine do ADR-015).
* Endpoint agregado `GET /api/v1/dashboard/summary`.
* Tela "Dashboard Executivo" no frontend.
* Endpoint(s) de exportacao PDF.

Resultado Esperado:

Visao executiva e relatorios exportaveis, sem mudanca de arquitetura nem dependencia externa nova.

Validado em 2026-08-11: suite completa do backend com 96 testes passando e build de producao do frontend (`npm run build`) com Postgres local via Docker Compose. EPIC 20 encerrada.

---

# Fase 18

Observabilidade de Infraestrutura (Prometheus + Grafana) — planejamento concluido (ADR-030), implementacao pendente

Meta:

Monitorar o Edge Node e os containers, com escopo corrigido para nao duplicar o pipeline de metricas por maquina que o agente Windows ja mantem (Fase E, EPIC 3).

Entregas:

* `node_exporter` e cAdvisor (ou metricas nativas do Docker) no Compose de producao.
* Prometheus com scrape config; Grafana com dashboard(s) de saude do Edge Node.
* Prometheus/Grafana nao expostos publicamente (Nginx continua unico ponto de entrada).
* Validacao de impacto de recursos no free tier antes de ativar (`infra/scripts/ops-check.sh`).

Resultado Esperado:

Visibilidade operacional da infraestrutura sem aumentar a superficie publica nem duplicar responsabilidade com o agente.

---

# Fase 19

Auto-atualizacao do Agente Windows — planejamento concluido (ADR-032), implementacao pendente

Meta:

Implementar atualizacao automatica do agente Windows via um updater dedicado, 100% PowerShell puro, com Tarefa Agendada propria (`ITCenterAgentUpdater`) e frequencia menor que o check-in de coleta. Sem Servico Windows nativo via SCM, sem NSSM/WinSW. Resolve, apenas para este caso, o item "Criar servico Windows" da Fase B de `docs/architecture/FUTURE_ARCHITECTURE.md`; o caso geral (servico Windows para a coleta em si) continua pendente.

Entregas:

* Novo script `agent-windows/itcenter-agent-updater.ps1` com Tarefa Agendada dedicada, registrada por `install-agent.ps1`
* Endpoints `GET /api/v1/agent/manifest` e `GET /api/v1/agent/download`, autenticados por `X-Agent-Api-Key`
* Validacao obrigatoria de assinatura Authenticode (certificado do ADR-031) e hash SHA-256 antes de substituir o script, sem fallback de bypass
* Backup automatico (`itcenter-agent.ps1.previous`) e auto-rollback apos N falhas consecutivas de check-in
* Rollout controlado por `machines.target_agent_version` e visibilidade via `machines.agent_version`

Resultado Esperado:

Atualizacao do agente Windows sem intervencao manual por maquina, mantendo 100% PowerShell puro e sem Servico Windows via SCM. Somente planejamento/documentacao nesta rodada (EPIC 22 de `docs/development/TASKS.md`).
