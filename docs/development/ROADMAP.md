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
| Fase 20 | EPIC 23 |
| Fase 21 | EPIC 24 |
| Fase 22 | EPIC 25 |
| Fase 23 | EPIC 26 |
| Fase 24 | EPIC 27 |
| Fase 25 | EPIC 28 |
| Fase 26 | EPIC 29 |
| Fase 27 | EPIC 30 |
| Fase 28 | EPIC 31 |
| Fase 29 | EPIC 32 |
| Fase 30 | EPIC 33 |

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
EPIC 19 - Hub de Integracao: RustDesk (Snipe-IT implementado e revertido, ver ADR-033)
EPIC 20 - Relatorios PDF e Dashboard Executivo
EPIC 21 - Observabilidade de Infraestrutura (Prometheus + Grafana)
EPIC 22 - Auto-atualizacao do Agente Windows (Updater Dedicado)
EPIC 23 - Auto-deteccao do ID do RustDesk no Agente
EPIC 24 - Polimento Visual do Dashboard (GSAP)
EPIC 25 - Modernizacao Visual do Dashboard (Design DNA)
EPIC 26 - Layout Persistente de Autenticacao (Velocidade de Navegacao)
EPIC 27 - Numero de Serie da Maquina (Coleta pelo Agente)
EPIC 28 - Correcao de Achados de Seguranca (Auditoria Tecnica 2026-08-15)
EPIC 29 - Correcao de Confiabilidade Operacional (Auditoria Tecnica 2026-08-15)
EPIC 30 - Correcao de Integridade de Dados do Backend (Auditoria Tecnica 2026-08-15)
EPIC 31 - Correcao de Resiliencia do Agente Windows (Auditoria Tecnica 2026-08-15)
EPIC 32 - Correcao de Aderencia Documentacao-Codigo (Auditoria Tecnica 2026-08-15)
EPIC 33 - Cobertura de Testes (Auditoria Tecnica 2026-08-15)
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
users -> EPIC 12
audit_logs -> EPIC 12
machines.mac_address -> EPIC 4
machines.rustdesk_id -> EPIC 19
machines.serial_number -> EPIC 27
```

## API

`docs/backend/API.md`

```text
POST /api/v1/agent/checkin -> EPIC 2 e EPIC 4
GET /api/v1/machines/{id} -> EPIC 2
GET /api/v1/machines/{id}/metrics -> EPIC 2
GET /api/v1/machines/{id}/programs -> EPIC 2
PATCH /api/v1/alerts/{id}/resolve -> EPIC 2
POST /api/v1/auth/login -> EPIC 12
GET /api/v1/auth/me -> EPIC 12
POST /api/v1/auth/logout -> EPIC 12
PATCH /api/v1/machines/{id}/rustdesk -> EPIC 19
GET /api/v1/dashboard/summary -> EPIC 20
GET /api/v1/reports/executive.pdf -> EPIC 20
GET /api/v1/machines/{id}/report.pdf -> EPIC 20
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
MAC Address -> EPIC 4
Hardening (ACL, quarentena de cache, rotacao de logs, assinatura de codigo) -> EPIC 16
Numero de serie -> EPIC 27
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
ADR-016 -> topologia de producao em no unico `itcenter-edge-01` e dimensionamento da VCN (EPIC 7)
ADR-017 -> arquitetura operacional em camadas (Edge/Infra/Platform/Application/Data) e rede Docker `itcenter-network` (EPIC 7)
ADR-018 -> refatoracao da infraestrutura de producao (Dockerfiles, compose com healthchecks, scripts de preflight/deploy/rollback/backup/restore) (EPIC 7)
ADR-019 -> contratos operacionais minimos de producao (preflight obrigatorio, scripts versionados, logs em stdout/stderr) (EPIC 7)
ADR-020 -> GitHub Actions para CI automatico e deploy manual de producao via SSH (EPIC 13)
ADR-021 -> RBAC administrativo inicial com papeis admin/analyst/viewer, separado da autenticacao do agente (EPIC 12)
ADR-022 -> login administrativo com Bearer token HMAC SHA-256 e senha em PBKDF2-SHA256 (EPIC 12)
ADR-023 -> isencao das rotas `/api/backend/` do Basic Auth do Nginx para nao quebrar o Bearer token da aplicacao (EPIC 13)
ADR-024 -> Terraform via import para a camada de infraestrutura abaixo do SO (EPIC 15)
ADR-025 -> mantem o agente Windows em PowerShell, Go como candidata condicional a reescrita futura (EPIC 16)
ADR-026 -> orquestracao de agentes de IA com recursos nativos do Claude Code
ADR-027 -> RustDesk como acesso remoto integrado (EPIC 19)
ADR-028 -> integracao com Snipe-IT como fonte de ITAM (EPIC 19) - revertida, ver ADR-033
ADR-029 -> ReportLab para relatorios PDF e dashboard executivo (EPIC 20)
ADR-030 -> Prometheus + Grafana para observabilidade de infraestrutura (EPIC 21)
ADR-031 -> certificado self-signed + ExecutionPolicy AllSigned para assinatura de codigo do agente Windows (EPIC 16)
ADR-032 -> updater dedicado (Tarefa Agendada propria) para auto-atualizacao do agente Windows (EPIC 22)
ADR-033 -> reversao da integracao Snipe-IT (EPIC 19), sem Snipe-IT real conectado em producao
ADR-034 -> auto-deteccao do ID do RustDesk pelo agente Windows, planejamento (EPIC 23)
ADR-035 -> GSAP para polimento visual do dashboard, escolhido sobre Three.js (EPIC 24)
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

Infraestrutura como Codigo — quase concluida (ADR-024), 2 pendencias bloqueadas por acesso a conta Oracle Cloud

Meta:

Provisionar e versionar via Terraform a camada de infraestrutura Oracle Cloud sem destruir o ambiente de producao existente.

Entregas:

* Modulos Terraform (network e compute)
* Import dos recursos existentes, com `terraform plan` em "No changes." (concluido em 2026-08-04)
* Documentacao de shape, availability domain, regiao e compartment antes ausente (concluido)
* Scripts de bootstrap (`infra/bootstrap/{01-system,02-packages,03-directories,04-docker,05-firewall,bootstrap}.sh`) conforme `docs/deployment/BOOTSTRAP.md` (implementados em 2026-08-15, nao executados contra a VM real — so tem efeito numa VM nova ou recuperacao de desastre)
* Variavel opcional de cloud-init/bootstrap no module compute, documentada e cross-referenciada (sem ativar em producao)

Pendente (2 itens, ambos **BLOQUEADOS em 2026-08-15** pela perda de acesso ao unico usuario administrador da tenancy Oracle Cloud — sem MFA de backup nem segundo administrador; ver `docs/deployment/KNOWN_ISSUES.md`, "Acesso ao Console Oracle Cloud bloqueado", e progresso em EPIC 15 de `docs/development/TASKS.md`):

* Bucket OCI Object Storage para state remoto
* Migracao do state para o backend remoto (`terraform init -migrate-state`) — bloqueada tambem por um segundo motivo: `terraform.tfvars`/`terraform.tfstate` do import de 2026-08-04 nao foram localizados, exigindo gerar API key nova e refazer a descoberta/import do zero antes de qualquer migracao

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

Hub de Integracao: RustDesk — concluida (ADR-027)

Meta:

Entregar as integracoes do Hub (Fase H de `docs/architecture/FUTURE_ARCHITECTURE.md`) priorizadas em 2026-08-03 por menor esforco e maior valor imediato: RustDesk (acesso remoto) e Snipe-IT (ITAM).

Entregas:

* RustDesk: coluna `machines.rustdesk_id`, endpoint `PATCH /api/v1/machines/{id}/rustdesk`, botao "Conectar" no detalhe da maquina, RBAC restrito a admin/analyst.
* Snipe-IT: implementado em 2026-08-04 (servico de integracao desacoplado, secrets, coluna `machines.snipeit_asset_id`, sincronizacao automatica no check-in, link no dashboard), mas **revertido em 2026-08-11** (ADR-033) — nunca existiu um Snipe-IT real conectado em producao, sem necessidade concreta de ITAM identificada. Volta a EPIC 14 (Melhorias Futuras) como item aspiracional.

Resultado Esperado:

Acesso remoto integrado ao dashboard sem o IT Center reimplementar essa especialidade. Inventario administrativo (ITAM) permanece uma lacuna conhecida, sem solucao ativa por ora.

Validado em 2026-08-11: suite completa do backend com 89 testes passando (`pytest`, PostgreSQL local via Docker Compose) apos a reversao do Snipe-IT. EPIC 19 encerrada, cobrindo apenas RustDesk.

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

Observabilidade de Infraestrutura (Prometheus + Grafana) — concluida (ADR-030)

Meta:

Monitorar o Edge Node e os containers, com escopo corrigido para nao duplicar o pipeline de metricas por maquina que o agente Windows ja mantem (Fase E, EPIC 3).

Entregas:

* `node_exporter` e cAdvisor no Compose de producao, sob `profiles: ["observability"]` (opt-in, mesmo padrao do `certbot`/`maintenance`)
* Prometheus com scrape config (`infra/observability/prometheus/prometheus.yml`, retencao `5d`/`200MB`) e Grafana com dashboard pre-configurado de saude do Edge Node
* Prometheus/Grafana nao expostos publicamente (Nginx continua unico ponto de entrada); acesso via `docker exec`/tunel SSH
* Revisao de seguranca corrigiu 2 achados altos (mount de `/var/run` no cAdvisor removido; risco residual do mount de `/` documentado em SECURITY.md) e 2 medios (imagens no gate do Docker Scout; `ops-check.sh` falha se `GRAFANA_ADMIN_PASSWORD` estiver no fallback)

Resultado Esperado:

Visibilidade operacional da infraestrutura sem aumentar a superficie publica nem duplicar responsabilidade com o agente.

Validado na VM real em 2026-08-15: os 4 containers subiram healthy via `docker compose --profile observability up -d`; `ops-check.sh` reportou `OK Operacao sem falhas criticas` (memoria da VM em `WARN`, risco aceito e documentado em `docs/deployment/KNOWN_ISSUES.md`). EPIC 21 de `docs/development/TASKS.md` encerrada.

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

---

# Fase 20

Auto-deteccao do ID do RustDesk no Agente — planejamento concluido (ADR-034), implementacao pendente

Meta:

Eliminar a digitacao manual do ID do RustDesk (ADR-027) sempre que possivel: o agente tenta ler o ID ja configurado no RustDesk instalado (arquivo `RustDesk2.toml` e/ou `RustDesk.exe --get-id`, ambos a testar de fato contra a versao real usada no ambiente antes de decidir qual usar) e envia-lo no check-in. O cadastro manual continua existindo e disponivel a qualquer momento — a deteccao automatica e um atalho, nunca uma dependencia.

Requisito explicito, herdado da licao da reversao do Snipe-IT (ADR-033): falha de leitura automatica, versao do RustDesk diferente da testada, ou instalacao em caminho nao previsto **nunca bloqueiam o check-in nem impedem o cadastro manual**.

Entregas:

* Validacao empirica dos dois metodos de leitura (arquivo de config vs. flag `--get-id`) contra a instalacao real, antes de fixar a abordagem
* Deteccao condicionada a RustDesk ja identificado como instalado (reaproveita deteccao existente em `app/services/agent.py`)
* `rustdesk_id` enviado no check-in quando a leitura automatica funcionar, reaproveitando campo/schema/coluna do ADR-027 (sem migration nova)
* Indicacao no dashboard da origem do dado (automatico vs. manual), sem remover o formulario de edicao manual

Resultado Esperado:

Menos fricção operacional no cadastro do RustDesk por maquina, sem enfraquecer a garantia de que o cadastro manual sempre funciona. Somente planejamento/documentacao nesta rodada (EPIC 23 de `docs/development/TASKS.md`).

---

# Fase 21

Polimento Visual do Dashboard (GSAP) — concluida (ADR-035)

Meta:

Adicionar animacoes de polimento (entrada de cards/paineis/linhas, contadores animados, preenchimento das barras de metrica) nas telas ja existentes, sem mudar logica de dados/API. Avaliadas GSAP e Three.js; GSAP escolhida por ser leve e ter encaixe direto com um app funcional que so precisa de polimento, nao de grafismo 3D (ADR-035).

Entregas:

* Skill oficial `greensock/gsap-skills` instalada (5 de 8 skills) antes de escrever qualquer animacao, garantindo uso correto da API
* `gsap`/`@gsap/react` + `frontend/dashboard/lib/motion.ts` (`useStaggerEntrance`, `animateCountUp`, `animateProgressValue`) — so `transform`/`opacity`, respeitando `prefers-reduced-motion` via `gsap.matchMedia()`
* Aplicado em `Shell.tsx`, `Ui.tsx`, `LoginView.tsx` e nas 6 telas de dados (Dashboard, Executivo, Maquinas, Alertas, Seguranca, Detalhe de Maquina)

Resultado Esperado:

Dashboard com a mesma funcionalidade, com polimento visual consistente em todas as telas. Validado via `npm run build` e smoke test das rotas autenticadas com dados reais; nao verificado visualmente em navegador real nesta rodada (sem ferramenta de automacao de browser conectada) — revisao visual manual recomendada antes de producao. EPIC 24 de `docs/development/TASKS.md` encerrada.

---

# Fase 22

Modernizacao Visual do Dashboard (Design DNA) — concluida

Meta:

Harmonizar o visual das 7 telas do dashboard (design system consistente), sem mudar logica de dados/API/RBAC — mesmo espirito da Fase 21. Referencia de inspiracao extraida via a skill `zanwei/design-dna` a partir de screenshots da demo publica do Snipe-IT (valor no padrao de organizacao, nao no acabamento visual — paleta propria do projeto foi mantida).

Entregas:

* Tokens semanticos unificados em `app/globals.css` (`--success`/`--warning`/`--danger`/`--info`/`--critical`), dark mode automatico via `prefers-color-scheme`
* `StatCard` com prop `tone`; novo componente `Panel` substituindo o padrao repetido `<section className="panel">`
* Aplicado nas 6 telas de dados (9 paineis), preservando o RBAC visual existente

Resultado Esperado:

Dashboard com aparencia consistente entre telas, sem alterar dado/API/RBAC. Validado via `npm run build`; nao verificado visualmente em navegador real (mesma limitacao da Fase 21). EPIC 25 de `docs/development/TASKS.md` encerrada.

---

# Fase 23

Layout Persistente de Autenticacao (Velocidade de Navegacao) — concluida

Meta:

Reduzir o tempo de carregamento percebido ao navegar entre telas: `Shell.tsx` nao vivia em um layout compartilhado do Next.js App Router, entao cada navegacao desmontava/remontava a sidebar inteira e refazia o fetch `GET /api/v1/auth/me`.

Entregas:

* `AuthProvider.tsx` (Context) buscando `/api/v1/auth/me` uma unica vez por sessao
* `Shell.tsx` -> `AppShell.tsx` (chrome persistente); paginas autenticadas movidas para `app/(authenticated)/` com layout unico
* Fetch duplicado de `/api/v1/auth/me` removido de `AlertsView`/`MachineDetailView`
* `middleware.ts` ganhou `/executive` no `matcher` (unica rota autenticada sem protecao server-side de cookie)

Resultado Esperado:

Navegacao mais rapida entre telas sem refazer autenticacao a cada clique, sem mudar URLs nem RBAC. Validado via `npm run build`; verificacao de rede em navegador real recomendada antes de producao. EPIC 26 de `docs/development/TASKS.md` encerrada.

---

# Fase 24

Numero de Serie da Maquina (Coleta pelo Agente) — quase concluida, 1 pendencia de validacao

Meta:

Coletar o numero de serie (service tag) via agente Windows para uso em inventario de ativos, com a mesma filosofia de resiliencia das demais integracoes do agente (falha na leitura nunca bloqueia o check-in).

Entregas:

* `Get-AgentSerialNumber`: tenta `Win32_BIOS.SerialNumber`, com fallback para `Win32_ComputerSystemProduct.IdentifyingNumber` quando vazio/placeholder — testado em maquina fisica real (2026-08-14)
* Coluna `machines.serial_number` (migration `008_machines_serial_number.sql`), persistida a cada check-in, exposta em `GET /api/v1/machines`/`{id}` e exibida no detalhe da maquina

Pendente (1 item; detalhes em EPIC 27 de `docs/development/TASKS.md`):

* Testar o mesmo campo contra maquina(s) virtual(is) — nao realizado por falta de VM disponivel no ambiente de testes; lista de placeholders (vazio, "System Serial Number", "To Be Filled By O.E.M." etc.) baseada em valores publicamente conhecidos, ainda nao validada empiricamente

Resultado Esperado:

Numero de serie disponivel no inventario sem digitacao manual quando o hardware expuser o dado via WMI/CIM. EPIC 27 **nao encerrada** ate a validacao contra VM.

---

# Fase 25

Correcao de Achados de Seguranca (Auditoria Tecnica 2026-08-15) — em andamento

Meta:

Corrigir os achados de seguranca da auditoria tecnica completa de 2026-08-15 (backend, frontend, agente Windows), com verificacao adversarial 1:1 por achado. Detalhes completos em EPIC 28 de `docs/development/TASKS.md`.

Entregas previstas:

* Vincular a identidade da maquina a algo alem do hostname autorreportado (severidade alta — personificacao de maquina via `AGENT_API_KEY` compartilhada) — pendente
* Corrigir bypass de path traversal via `%2f` no proxy do dashboard (severidade alta — expoe `/docs` da API sem autenticacao) — parcial: segunda camada no backend concluida (`docs_url`/`redoc_url`/`openapi_url` desativados quando `APP_ENV=production`); causa raiz no proxy do frontend segue pendente
* Equalizar tempo de resposta do login (severidade media — enumeracao de e-mail) — concluido em 2026-08-17
* Ler `X-Real-IP` em vez do primeiro valor de `X-Forwarded-For` em `audit_logs` (severidade media) — concluido em 2026-08-17
* Remover `unsafe-inline` de `script-src` na CSP do dashboard (severidade media) — pendente
* Restringir ACL de `logs\`/`cache\` do agente, nao so `config.json` (severidade media) — pendente
* Bloco `permissions:` restrito em `ci.yml` (severidade baixa) — pendente

Resultado Esperado:

Fechar os achados de seguranca mais graves identificados na auditoria antes de qualquer exposicao adicional do produto. Duas correcoes de backend concluidas e testadas (`pytest`, 93 passed); demais itens (personificacao de maquina, causa raiz do path traversal no proxy, CSP, ACL do agente, permissoes do CI) seguem pendentes.

---

# Fase 26

Correcao de Confiabilidade Operacional (Auditoria Tecnica 2026-08-15) — nao iniciada

Meta:

Corrigir os dois achados mais graves da auditoria tecnica de 2026-08-15: backup e restore podem reportar sucesso mesmo tendo falhado. Detalhes completos em EPIC 29 de `docs/development/TASKS.md`.

Entregas previstas:

* Corrigir falha silenciosa em `backup.sh` (pipe `pg_dump | gzip` nao propaga o exit code do `pg_dump`)
* Corrigir falha silenciosa em `restore.sh` (mesmo problema, agravado por rodar apos um `DROP SCHEMA public CASCADE` destrutivo e sem `-v ON_ERROR_STOP=1` no `psql`)
* Automatizar o gate de CVE do Docker Scout no deploy (hoje so documentado, nunca invocado por `ci.yml`/`deploy-production.yml`)

Resultado Esperado:

Backup/restore reportando sucesso somente quando de fato bem-sucedidos, e o gate de CVE deixando de depender de um humano lembrar de rodar manualmente. Nenhuma tarefa iniciada ate o momento.

---

# Fase 27

Correcao de Integridade de Dados do Backend (Auditoria Tecnica 2026-08-15) — nao iniciada

Meta:

Corrigir uma race condition que duplica alertas, um mismatch de constraint que pode derrubar o check-in inteiro, e consultas sem filtro/paginacao que crescem sem parar. Detalhes completos em EPIC 30 de `docs/development/TASKS.md`.

Entregas previstas:

* Indice parcial UNIQUE (ou `SELECT ... FOR UPDATE`) para evitar alertas abertos duplicados sob retry do agente
* Alinhar a constraint UNIQUE de `installed_programs` com a chave de dedup real do agente (incluir `publisher`)
* Filtrar por `machine_id` no SQL do relatorio PDF de maquina, em vez de filtrar em Python apos carregar tudo
* Paginacao em `/alerts`, `/security-events` e `/machines/{id}/metrics`
* Indice composto para a query de existencia de alerta (`machine_id`, `alert_type`, `status`)
* Identidade de admin local case-insensitive de ponta a ponta (indice sobre `lower(admin_name)`)
* Deduplicar deteccao de VPN/torrent dentro do mesmo check-in; validar formato de `ip_address` no schema

Resultado Esperado:

Dados consistentes mesmo sob retry/concorrencia, e listagens que nao crescem sem limite na VM de 1GB. Nenhuma tarefa iniciada ate o momento.

---

# Fase 28

Correcao de Resiliencia do Agente Windows (Auditoria Tecnica 2026-08-15) — nao iniciada

Meta:

Corrigir gaps de resiliencia do agente Windows, mantendo a filosofia de robustez ja aplicada no hardening da Fase 13 (EPIC 16): falha em uma coleta nunca deve travar o check-in inteiro. Detalhes completos em EPIC 31 de `docs/development/TASKS.md`.

Entregas previstas:

* Try/catch proprio em `Get-AgentLocalAdmins` (severidade alta — excecao terminante hoje derruba o check-in inteiro, maquina some do dashboard)
* Consultar o usuario do console interativo em vez do processo (severidade media — Tarefa Agendada roda como SYSTEM, todo check-in reporta "NT AUTHORITY\SYSTEM")
* Lock ao redor do envio de cache pendente (severidade media — execucao manual concorrente com o ciclo agendado pode abandonar a fila)
* Excluir adaptadores virtuais/VPN da selecao de IP (severidade baixa)

Resultado Esperado:

Agente Windows que nunca some do dashboard por falha de coleta isolada, e que reporta o usuario real em vez de SYSTEM. Nenhuma tarefa iniciada ate o momento.

---

# Fase 29

Correcao de Aderencia Documentacao-Codigo (Auditoria Tecnica 2026-08-15) — em andamento

Meta:

Corrigir divergencias entre documentacao e codigo real encontradas na auditoria tecnica de 2026-08-15. Detalhes completos em EPIC 32 de `docs/development/TASKS.md`.

Entregas:

* Documentado (2026-08-17) que os endpoints de PDF tambem disparam `mark_stale_machines_offline`, em `docs/backend/API.md`
* Atualizada (2026-08-17) a allowlist documentada do proxy em `docs/security/SECURITY.md` para os 9 prefixos reais de `ALLOWED_PATH_PREFIXES` (antes listava so 5)

Pendente (1 item):

* Resolver a divergencia entre `API.md` e `SOC_RULES.md` sobre deteccao de VPN/torrent em processos — exige decidir entre estender a checagem de processos (fechando uma lacuna real de deteccao) ou so corrigir a doc; decisao de escopo de codigo, nao resolvida nesta rodada de documentacao

Resultado Esperado:

Documentacao tecnica confiavel para quem decide com base nela, sem lacuna de deteccao SOC real esquecida.

---

# Fase 30

Cobertura de Testes (Auditoria Tecnica 2026-08-15) — nao iniciada

Meta:

Fechar lacunas de cobertura de teste encontradas na auditoria tecnica de 2026-08-15: uma regra SOC sem nenhum teste, e duas garantias de comportamento de seguranca nunca exercitadas. Detalhes completos em EPIC 33 de `docs/development/TASKS.md`.

Entregas previstas:

* Teste de fronteira para a regra SOC `failed_login` (5 nao alerta, 6 alerta) — unica das 14 regras SOC sem teste dedicado
* Teste de idempotencia de `apply_migrations()` (aplicar o conjunto completo duas vezes seguidas contra um banco limpo)
* Teste de revogacao de sessao em tempo real (emitir token, desabilitar usuario, confirmar 401 na proxima requisicao)
* Incluir e testar o campo usuario no evento de USB (`payload.username` ausente hoje em `raw_data`/descricao, exigido pela Regra 6 de `SOC_RULES.md`)

Resultado Esperado:

Cobertura de teste que barra regressao nas garantias de seguranca ja implementadas, mas nunca verificadas por CI. Nenhuma tarefa iniciada ate o momento.
