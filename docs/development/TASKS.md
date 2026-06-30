# TASKS.md

# Backlog Oficial

## Status

Legenda:

[ ] Não iniciado

[~] Em andamento

[x] Concluído

---

# EPIC 1 - Fundação do Projeto

Objetivo:

Criar a estrutura base do projeto.

### Tarefas

[x] Criar repositório GitHub

[x] Criar estrutura de diretórios

[x] Criar README.md

[x] Criar ROADMAP.md e TASKS.md

[x] Criar docs/architecture/ARCHITECTURE.md

[x] Criar docs/backend/DATABASE.md

[x] Criar docs/backend/API.md

[x] Criar docs/agent/CHECKIN.md

[x] Criar docs/security/SECURITY.md

[x] Criar docs/security/SOC_RULES.md

[x] Criar docs/security/ASSET_POLICY.md

[x] Criar docs/development/DECISIONS.md

---

# EPIC 2 - Backend

Objetivo:

Criar API funcional.

### Tarefas

[x] Criar projeto FastAPI

[x] Configurar ambiente Python

[x] Criar endpoint /health

[x] Criar endpoint /agent/checkin

[x] Criar endpoint /machines

[x] Criar endpoint /machines/{id}

[x] Criar endpoint /machines/{id}/metrics

[x] Criar endpoint /machines/{id}/programs

[x] Criar endpoint /alerts

[x] Criar endpoint /alerts/{id}/resolve

[x] Criar endpoint /security-events

---

# EPIC 3 - Banco

Objetivo:

Persistência de dados.

### Tarefas

[x] Criar PostgreSQL

[x] Criar Docker para PostgreSQL

[x] Criar tabela machines

[x] Criar tabela metrics

[x] Criar tabela installed_programs

[x] Criar tabela security_events

[x] Criar tabela alerts

[x] Criar tabela agent_configs

[x] Criar migrations

[x] Integrar API ao PostgreSQL

[x] Persistir check-in em machines, metrics e installed_programs

[x] Ler machines, alerts e security_events do PostgreSQL

[x] Persistir agent_configs

---

# EPIC 4 - Agente Windows

Objetivo:

Coleta de informações.

### Tarefas

[x] Criar estrutura do agente

[x] Criar config.json

[x] Coletar hostname

[x] Coletar usuário

[x] Coletar IP

[x] Coletar sistema operacional

[x] Coletar programas instalados

[x] Coletar uptime

[x] Coletar CPU

[x] Coletar RAM

[x] Coletar disco

[x] Gerar JSON

[x] Enviar para API

[x] Cache offline

[x] Reenviar dados em caso de falha

---

# EPIC 5 - Dashboard

Objetivo:

Visualização inicial.

### Tarefas

[x] Criar projeto Next.js

[x] Criar tela Dashboard

[x] Criar tela Máquinas

[x] Criar tela Alertas

[x] Criar tela Segurança

[x] Consumir API

---

# EPIC 6 - SOC Light

Objetivo:

Primeiras detecções.

### Tarefas

[x] Detectar Firewall

[x] Detectar Defender

[x] Detectar RDP

[x] Detectar USB

[x] Detectar Administradores Locais

[x] Detectar Ferramentas Remotas

[x] Gerar Eventos

[x] Gerar Alertas

---

# EPIC 7 - Produção

Objetivo:

Primeiro deploy.

### Tarefas

[x] Criar VM Oracle

[x] Instalar Docker

[x] Configurar PostgreSQL

[x] Configurar Nginx

[x] Configurar HTTPS

[x] Publicar Backend

[x] Publicar Frontend

---

# EPIC 8 - Agente Windows em Produção

Objetivo:

Transformar o agente PowerShell em um componente operacional, instalavel e validado contra o ambiente publicado.

### Tarefas

[x] Validar check-in do agente contra a URL publica de producao

[x] Validar envio do header X-Agent-Api-Key em producao

[ ] Validar persistencia do primeiro check-in real no PostgreSQL

[ ] Validar que a maquina aparece no dashboard publicado

[x] Criar script de instalacao do agente

[x] Criar script de desinstalacao do agente

[x] Registrar o agente como servico Windows ou tarefa agendada controlada

[x] Definir local padrao de instalacao no Windows

[x] Definir local padrao de logs do agente

[x] Definir local padrao de cache offline do agente

[x] Padronizar config.json do agente para producao

[ ] Validar ciclo periodico de check-in

[ ] Melhorar retry inteligente em falhas temporarias

[x] Garantir que cache offline nao armazene dados proibidos

[x] Documentar instalacao real em docs/agent/INSTALLATION.md

[ ] Documentar troubleshooting do agente

---

# EPIC 9 - Validação do Fluxo Fim a Fim

Objetivo:

Provar o fluxo completo entre agente, Nginx, FastAPI, PostgreSQL e dashboard com dados reais.

Observacao de validacao:

Em 2026-06-29, `python -m pytest backend\tests\test_agent_checkin.py -q` passou com PostgreSQL local via Docker Compose: 9 testes aprovados. O teste `test_agent_checkin_persists_full_operational_snapshot` cobre a persistencia do snapshot operacional em `machines`, `metrics`, `installed_programs`, `machine_local_admins` e `agent_configs`, alem das rotas de leitura usadas pelo dashboard.

### Tarefas

[x] Executar check-in real a partir de uma maquina Windows

[x] Confirmar recebimento pelo Nginx em HTTPS

[x] Confirmar validacao de X-Agent-Api-Key no backend

[x] Confirmar gravacao em machines

[x] Confirmar gravacao em metrics

[x] Confirmar gravacao em installed_programs

[x] Confirmar sincronizacao de machine_local_admins

[x] Confirmar criacao de agent_configs no primeiro check-in

[x] Confirmar geracao de security_events

[x] Confirmar geracao de alerts quando houver risco

[ ] Confirmar exibicao dos dados no dashboard

[ ] Registrar evidencias do teste em docs/deployment/DEPLOYMENT_HISTORY.md

[ ] Atualizar docs/deployment/KNOWN_ISSUES.md se houver falha conhecida

---

# EPIC 10 - Dashboard Operacional

Objetivo:

Evoluir o dashboard de visualizacao inicial para uma ferramenta de operacao diaria.

### Tarefas

[ ] Melhorar tela de detalhes da maquina

[ ] Exibir historico de metricas por maquina

[x] Exibir programas instalados por maquina

[ ] Exibir administradores locais por maquina

[ ] Exibir eventos de seguranca por maquina

[x] Permitir resolver alertas pela interface

[x] Adicionar filtros por severidade

[x] Adicionar filtros por tipo de evento

[x] Adicionar filtros por maquina

[ ] Melhorar estados vazios quando nao houver agente

[ ] Melhorar indicacao de maquina online e offline

[ ] Validar responsividade das telas principais

[ ] Atualizar docs/backend/API.md se novas chamadas forem necessarias

---

# EPIC 11 - SOC Light Pendências

Objetivo:

Concluir regras SOC ja definidas e preparar a politica para configuracao operacional.

### Tarefas

[ ] Implementar regra unknown_asset

[ ] Implementar regra machine_offline

[ ] Definir criterio oficial de maquina conhecida

[x] Definir janela oficial para maquina offline

[ ] Melhorar validacao de RDP autorizado por politica

[ ] Melhorar validacao de ferramenta remota autorizada por politica

[x] Evitar duplicidade indevida de alertas abertos

[ ] Criar testes para unknown_asset

[ ] Criar testes para machine_offline

[ ] Atualizar docs/security/SOC_RULES.md com o status das regras

[ ] Atualizar docs/security/ASSET_POLICY.md se novas listas forem necessarias

---

# EPIC 12 - Governança e Autenticação

Objetivo:

Substituir controles minimos do MVP por autenticacao e governanca adequadas para uso administrativo.

### Tarefas

[ ] Definir modelo de usuarios

[ ] Definir modelo de permissoes

[ ] Criar tabela users

[ ] Criar tabela audit_logs

[ ] Implementar login

[ ] Implementar sessoes ou JWT

[ ] Proteger rotas administrativas do backend

[ ] Proteger paginas administrativas do dashboard

[ ] Registrar auditoria de acoes criticas

[ ] Planejar rotacao de AGENT_API_KEY

[ ] Planejar API Key por agente

[ ] Atualizar docs/security/AUTH.md

[ ] Registrar decisoes relevantes em docs/development/DECISIONS.md

---

# EPIC 13 - Operação e Segurança de Produção

Objetivo:

Reduzir risco operacional do ambiente publicado e preparar manutencao continua.

### Tarefas

[ ] Automatizar backup periodico do PostgreSQL

[ ] Testar restore em ambiente controlado

[ ] Validar rollback de deploy

[ ] Validar renovacao de certificado TLS

[ ] Monitorar uso de disco da VM

[ ] Monitorar uso de memoria da VM

[ ] Monitorar containers unhealthy

[ ] Criar alerta para expiracao de certificado

[ ] Executar Docker Scout antes de publicar imagens

[x] Criar CI automatico no GitHub Actions

[x] Criar deploy manual de producao no GitHub Actions

[ ] Documentar rotina operacional semanal

[ ] Atualizar docs/deployment/TROUBLESHOOTING.md com novos cenarios

[ ] Atualizar docs/deployment/POSTMORTEMS.md quando houver incidente

---

# EPIC 14 - Melhorias Futuras

Objetivo:

Registrar evolucoes de produto fora do escopo operacional imediato.

### Tarefas

[ ] Wazuh

[ ] OpenVAS

[ ] Multiempresa

[ ] Relatorios PDF

[ ] Dashboard Executivo

[ ] Integracao Microsoft 365

[ ] Integracao Active Directory

[ ] Vulnerability Management

[ ] Billing

[ ] SaaS
