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
