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

[ ] Criar projeto FastAPI

[ ] Configurar ambiente Python

[ ] Criar endpoint /health

[ ] Criar endpoint /agent/checkin

[ ] Criar endpoint /machines

[ ] Criar endpoint /alerts

[ ] Criar endpoint /security-events

---

# EPIC 3 - Banco

Objetivo:

Persistência de dados.

### Tarefas

[ ] Criar PostgreSQL

[ ] Criar Docker para PostgreSQL

[ ] Criar tabela machines

[ ] Criar tabela metrics

[ ] Criar tabela installed_programs

[ ] Criar tabela security_events

[ ] Criar tabela alerts

[ ] Criar migrations

---

# EPIC 4 - Agente Windows

Objetivo:

Coleta de informações.

### Tarefas

[ ] Criar estrutura do agente

[ ] Criar config.json

[ ] Coletar hostname

[ ] Coletar usuário

[ ] Coletar IP

[ ] Coletar CPU

[ ] Coletar RAM

[ ] Coletar disco

[ ] Gerar JSON

[ ] Enviar para API

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
