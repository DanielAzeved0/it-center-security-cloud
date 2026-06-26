# ROADMAP.md

# Roadmap Oficial

## Objetivo

Guiar a evolução do IT Center Security Cloud.

---

# Matriz de Rastreabilidade

Esta seção liga o planejamento oficial às tarefas do backlog.

## Planejamento de Produto

`PROJECT_PLAN.md`

```text
EPIC 1 - Fundação do Projeto
EPIC 2 - Backend
EPIC 3 - Banco
EPIC 4 - Agente Windows
EPIC 5 - Dashboard
EPIC 6 - SOC Light
EPIC 7 - Produção
EPIC 8 - Melhorias Futuras
```

## Arquitetura

`ARCHITECTURE.md`

```text
Inventário do agente -> EPIC 4
Persistência API/PostgreSQL -> EPIC 2 e EPIC 3
Endpoints do backend -> EPIC 2
Estrutura do dashboard -> EPIC 5
Deploy e containers -> EPIC 7
```

## Banco

`DATABASE.md`

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

`API.md`

```text
POST /api/v1/agent/checkin -> EPIC 2 e EPIC 4
GET /api/v1/machines/{id} -> EPIC 2
GET /api/v1/machines/{id}/metrics -> EPIC 2
GET /api/v1/machines/{id}/programs -> EPIC 2
PATCH /api/v1/alerts/{id}/resolve -> EPIC 2
```

## Agente

`AGENT.md`

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
```

## SOC Light

`SOC_RULES.md`

```text
Firewall, Defender e RDP -> EPIC 6
USB e falhas de login -> EPIC 6
Administradores locais -> EPIC 6
Ferramentas remotas, VPN e torrent -> EPIC 6
Eventos e alertas -> EPIC 6
```

## Decisões

`DECISIONS.md`

```text
ADR-013 -> mantém a integração direta FastAPI + PostgreSQL
ADR-014 -> padroniza execução local integrada com Docker Compose
ADR-015 -> padroniza gate de seguranca das imagens Docker
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

Concluido.

---

# Fase 5

Deploy Cloud

Meta:

Sistema disponível externamente.

Entregas:

* Oracle Cloud
* HTTPS
* Docker

Resultado Esperado:

Primeira versão pública.

---

# Fase 6

Governança

Meta:

Adicionar controle operacional.

Entregas:

* Login
* Perfis
* Auditoria

Resultado Esperado:

Controle administrativo.

---

# Fase 7

SOC Avançado

Meta:

Evoluir para Blue Team.

Entregas:

* Wazuh
* IOC Detection
* Correlação
* MITRE ATT&CK

Resultado Esperado:

SOC corporativo.

---

# Fase 8

SaaS

Meta:

Transformar em produto.

Entregas:

* Multiempresa
* Multiusuário
* Billing
* Gestão de clientes

Resultado Esperado:

Produto comercializável.
