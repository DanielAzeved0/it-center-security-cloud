# ROADMAP.md

# Roadmap Oficial

## Objetivo

Guiar a evolução do IT Center Security Cloud.

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

Infraestrutura como Codigo

Meta:

Provisionar e versionar via Terraform a camada de infraestrutura Oracle Cloud sem destruir o ambiente de producao existente.

Entregas:

* Modulos Terraform (network e compute)
* Import dos recursos existentes
* Plan zero-diff validado
* Backend remoto em OCI Object Storage
* Documentacao de shape, availability domain, regiao e compartment antes ausente

Resultado Esperado:

Infraestrutura reproduzivel e auditavel em codigo, sem alterar o fluxo de deploy da aplicacao existente.

---

# Fase 13

Hardening do Agente Windows

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
* Scripts assinados e ExecutionPolicy mais restritiva

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
