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

[x] Criar PROJECT_PLAN.md

[x] Criar ARCHITECTURE.md

[x] Criar DATABASE.md

[x] Criar API.md

[x] Criar AGENT.md

[x] Criar SECURITY.md

[x] Criar SOC_RULES.md

[x] Criar ASSET_POLICY.md

[x] Criar DECISIONS.md

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

[ ] Criar endpoint /machines/{id}

[ ] Criar endpoint /machines/{id}/metrics

[ ] Criar endpoint /machines/{id}/programs

[x] Criar endpoint /alerts

[ ] Criar endpoint /alerts/{id}/resolve

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

[ ] Criar tabela agent_configs

[x] Criar migrations

[x] Integrar API ao PostgreSQL

[x] Persistir check-in em machines, metrics e installed_programs

[x] Ler machines, alerts e security_events do PostgreSQL

[ ] Persistir agent_configs

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

[ ] Coletar uptime

[x] Coletar CPU

[x] Coletar RAM

[x] Coletar disco

[x] Gerar JSON

[x] Enviar para API

[ ] Cache offline

[ ] Reenviar dados em caso de falha

---

# EPIC 5 - Dashboard

Objetivo:

Visualização inicial.

### Tarefas

[ ] Criar projeto Next.js

[ ] Criar tela Dashboard

[ ] Criar tela Máquinas

[ ] Criar tela Alertas

[ ] Criar tela Segurança

[ ] Consumir API

---

# EPIC 6 - SOC Light

Objetivo:

Primeiras detecções.

### Tarefas

[ ] Detectar Firewall

[ ] Detectar Defender

[ ] Detectar RDP

[ ] Detectar USB

[ ] Detectar Administradores Locais

[ ] Detectar Ferramentas Remotas

[ ] Gerar Eventos

[ ] Gerar Alertas

---

# EPIC 7 - Produção

Objetivo:

Primeiro deploy.

### Tarefas

[ ] Criar VM Oracle

[ ] Instalar Docker

[ ] Configurar PostgreSQL

[ ] Configurar Nginx

[ ] Configurar HTTPS

[ ] Publicar Backend

[ ] Publicar Frontend

---

# EPIC 8 - Melhorias Futuras

[ ] Wazuh

[ ] OpenVAS

[ ] Multiempresa

[ ] Login com JWT

[ ] API Key por Agente

[ ] Relatórios PDF

[ ] Dashboard Executivo
