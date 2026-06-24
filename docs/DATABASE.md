# DATABASE.md

# IT Center Security Cloud - Banco de Dados

## Objetivo

Definir a estrutura inicial do banco de dados PostgreSQL do IT Center Security Cloud.

O banco será responsável por armazenar:

* Máquinas monitoradas
* Métricas de desempenho
* Programas instalados
* Eventos de segurança
* Alertas
* Configurações dos agentes

---

# Banco Oficial

Tecnologia:

```text
PostgreSQL
```

Motivos:

* Gratuito
* Robusto
* Usado em produção
* Compatível com Docker
* Fácil integração com FastAPI

---

# Modelo Geral

```text
machines
   ↓
metrics

machines
   ↓
installed_programs

machines
   ↓
security_events

machines
   ↓
alerts

machines
   ↓
agent_configs
```

---

# Tabela: machines

Armazena os computadores e servidores cadastrados.

## Campos

```text
id
hostname
username
ip_address
operating_system
os_version
status
last_seen
created_at
updated_at
```

## Regras

* Cada máquina deve ter um hostname único.
* O status pode ser online ou offline.
* last_seen será atualizado a cada check-in do agente.

---

# Tabela: metrics

Armazena métricas de desempenho enviadas pelo agente.

## Campos

```text
id
machine_id
cpu_usage
ram_usage
disk_usage
uptime_seconds
created_at
```

## Regras

* Cada registro representa uma coleta.
* A tabela pode crescer bastante.
* No futuro, pode ter limpeza automática de dados antigos.

---

# Tabela: installed_programs

Armazena os programas instalados nas máquinas.

## Campos

```text
id
machine_id
name
version
publisher
installed_at
created_at
```

## Regras

* Relacionada com a máquina.
* Pode ser atualizada a cada inventário completo.
* Será usada para detectar softwares suspeitos.

---

# Tabela: security_events

Armazena eventos de segurança coletados ou gerados pelo sistema.

## Campos

```text
id
machine_id
event_type
severity
source
description
raw_data
created_at
```

## Exemplos de event_type

```text
failed_login
usb_detected
new_admin_user
firewall_disabled
defender_disabled
rdp_enabled
suspicious_software
```

## Exemplos de severity

```text
low
medium
high
critical
```

---

# Tabela: alerts

Armazena alertas criados a partir de eventos ou regras.

## Campos

```text
id
machine_id
alert_type
severity
status
title
description
created_at
resolved_at
```

## Exemplos de status

```text
open
investigating
resolved
ignored
```

---

# Tabela: agent_configs

Armazena configurações específicas dos agentes.

## Campos

```text
id
machine_id
agent_version
checkin_interval_minutes
collect_inventory
collect_security
collect_metrics
created_at
updated_at
```

---

# Índices Recomendados

## machines

```text
hostname
status
last_seen
```

## metrics

```text
machine_id
created_at
```

## security_events

```text
machine_id
event_type
severity
created_at
```

## alerts

```text
machine_id
status
severity
created_at
```

---

# Relacionamentos

## machines → metrics

Uma máquina pode ter muitas métricas.

```text
machines.id = metrics.machine_id
```

---

## machines → installed_programs

Uma máquina pode ter muitos programas instalados.

```text
machines.id = installed_programs.machine_id
```

---

## machines → security_events

Uma máquina pode ter muitos eventos de segurança.

```text
machines.id = security_events.machine_id
```

---

## machines → alerts

Uma máquina pode ter muitos alertas.

```text
machines.id = alerts.machine_id
```

---

## machines → agent_configs

Uma máquina pode ter uma configuração de agente.

```text
machines.id = agent_configs.machine_id
```

---

# Estratégia de Retenção

## MVP

Durante o MVP, não vamos apagar dados automaticamente.

## Futuro

Criar rotina para:

```text
Manter métricas detalhadas por 30 dias
Manter eventos de segurança por 180 dias
Manter alertas por 365 dias
```

---

# Segurança dos Dados

## Dados Sensíveis

O sistema pode armazenar:

```text
Hostname
Usuário logado
IP
Programas instalados
Eventos de segurança
```

Por isso:

* Não armazenar senhas.
* Não armazenar arquivos pessoais.
* Não coletar histórico de navegação.
* Não coletar conteúdo de documentos.
* Não coletar dados além do necessário.

---

# Tabelas Futuras

## users

Para login no dashboard.

## organizations

Para suporte SaaS no futuro.

## audit_logs

Para registrar ações feitas no painel.

## integrations

Para integração com e-mail, Telegram, Slack ou webhook.

## vulnerabilities

Para integração futura com OpenVAS.

---

# Critério de Conclusão

O banco inicial estará pronto quando existirem as tabelas:

* machines
* metrics
* installed_programs
* security_events
* alerts
* agent_configs

e todas estiverem relacionadas corretamente com machine_id.
