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
id BIGSERIAL PRIMARY KEY
hostname VARCHAR(255) NOT NULL UNIQUE
username VARCHAR(255) NULL
ip_address INET NULL
operating_system VARCHAR(255) NULL
os_version VARCHAR(100) NULL
status VARCHAR(20) NOT NULL DEFAULT 'offline'
last_seen TIMESTAMPTZ NULL
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
```

## Regras

* Cada máquina deve ter um hostname único.
* O status pode ser online ou offline.
* last_seen será atualizado a cada check-in do agente.
* status deve aceitar apenas: online, offline.
* hostname deve ser normalizado antes da gravação para evitar duplicidade por diferença de caixa.

---

# Tabela: metrics

Armazena métricas de desempenho enviadas pelo agente.

## Campos

```text
id BIGSERIAL PRIMARY KEY
machine_id BIGINT NOT NULL REFERENCES machines(id) ON DELETE CASCADE
cpu_usage NUMERIC(5,2) NOT NULL
ram_usage NUMERIC(5,2) NOT NULL
disk_usage NUMERIC(5,2) NOT NULL
uptime_seconds BIGINT NOT NULL
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
```

## Regras

* Cada registro representa uma coleta.
* A tabela pode crescer bastante.
* No futuro, pode ter limpeza automática de dados antigos.
* cpu_usage, ram_usage e disk_usage devem aceitar valores entre 0 e 100.
* uptime_seconds deve ser maior ou igual a 0.

---

# Tabela: installed_programs

Armazena os programas instalados nas máquinas.

## Campos

```text
id BIGSERIAL PRIMARY KEY
machine_id BIGINT NOT NULL REFERENCES machines(id) ON DELETE CASCADE
name VARCHAR(255) NOT NULL
version VARCHAR(100) NULL
publisher VARCHAR(255) NULL
installed_at TIMESTAMPTZ NULL
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
```

## Regras

* Relacionada com a máquina.
* No MVP, representa o estado atual conhecido dos programas instalados.
* A cada inventário completo, a API deve substituir o conjunto de programas da máquina por um novo snapshot.
* A data installed_at é opcional porque nem todo Windows informa essa data de forma confiável.
* Será usada para detectar softwares monitorados conforme ASSET_POLICY.md e SOC_RULES.md.
* Não deve existir duplicidade de name e version para a mesma máquina.

---

# Tabela: security_events

Armazena eventos de segurança coletados ou gerados pelo sistema.

## Campos

```text
id BIGSERIAL PRIMARY KEY
machine_id BIGINT NULL REFERENCES machines(id) ON DELETE SET NULL
event_type VARCHAR(100) NOT NULL
severity VARCHAR(20) NOT NULL
source VARCHAR(50) NOT NULL
description TEXT NOT NULL
raw_data JSONB NULL
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
```

## Exemplos de event_type

```text
failed_login
usb_detected
new_admin_user
firewall_disabled
defender_disabled
rdp_enabled
remote_access_tool_detected
unauthorized_remote_access_tool
unauthorized_vpn_tool
torrent_software_detected
```

## Exemplos de severity

```text
low
medium
high
critical
```

## Regras

* severity deve aceitar apenas: low, medium, high, critical.
* source deve aceitar inicialmente: agent, api, system.
* raw_data deve guardar apenas metadados técnicos permitidos, nunca senhas, cookies, arquivos pessoais ou conteúdo de documentos.

---

# Tabela: alerts

Armazena alertas criados a partir de eventos ou regras.

## Campos

```text
id BIGSERIAL PRIMARY KEY
machine_id BIGINT NULL REFERENCES machines(id) ON DELETE SET NULL
alert_type VARCHAR(100) NOT NULL
severity VARCHAR(20) NOT NULL
status VARCHAR(20) NOT NULL DEFAULT 'open'
title VARCHAR(255) NOT NULL
description TEXT NOT NULL
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
resolved_at TIMESTAMPTZ NULL
```

## Exemplos de status

```text
open
investigating
resolved
ignored
```

## Regras

* severity deve aceitar apenas: low, medium, high, critical.
* status deve aceitar apenas: open, investigating, resolved, ignored.
* resolved_at só deve ser preenchido quando status for resolved ou ignored.

---

# Tabela: agent_configs

Armazena configurações específicas dos agentes.

## Campos

```text
id BIGSERIAL PRIMARY KEY
machine_id BIGINT NOT NULL UNIQUE REFERENCES machines(id) ON DELETE CASCADE
agent_version VARCHAR(50) NULL
checkin_interval_minutes INTEGER NOT NULL DEFAULT 5
collect_inventory BOOLEAN NOT NULL DEFAULT true
collect_security BOOLEAN NOT NULL DEFAULT true
collect_metrics BOOLEAN NOT NULL DEFAULT true
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
```

## Regras

* Cada máquina pode ter no máximo uma configuração ativa de agente.
* checkin_interval_minutes deve ser maior que 0.
* A API Key do agente não deve ser armazenada nesta tabela em texto plano.

---

# Índices Recomendados

## machines

```text
UNIQUE hostname
INDEX status
INDEX last_seen
```

## metrics

```text
INDEX machine_id
INDEX created_at
INDEX machine_id, created_at
CHECK cpu_usage BETWEEN 0 AND 100
CHECK ram_usage BETWEEN 0 AND 100
CHECK disk_usage BETWEEN 0 AND 100
```

## installed_programs

```text
INDEX machine_id
UNIQUE machine_id, name, version
```

## security_events

```text
INDEX machine_id
INDEX event_type
INDEX severity
INDEX created_at
INDEX machine_id, created_at
```

## alerts

```text
INDEX machine_id
INDEX status
INDEX severity
INDEX created_at
INDEX status, severity
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

# Integração API e Banco

O backend acessa o PostgreSQL pela camada `repositories`.

## Check-in do Agente

Quando `POST /api/v1/agent/checkin` recebe payload válido:

```text
1. Normaliza hostname para caixa alta.
2. Cria ou atualiza machines usando hostname como chave única.
3. Define status como online.
4. Atualiza last_seen com now().
5. Insere uma nova coleta em metrics.
6. Remove os programas anteriores da máquina em installed_programs.
7. Insere o snapshot atual de installed_programs recebido no payload.
```

## Consultas

```text
GET /api/v1/machines lê machines.
GET /api/v1/alerts lê alerts.
GET /api/v1/security-events lê security_events.
```

## Configuração

O backend usa a variável:

```text
DATABASE_URL
```

Valor local padrão:

```text
postgresql://itcenter:change-me@127.0.0.1:5432/it_center_security_cloud
```

## Testes

Os testes de backend limpam as tabelas com `TRUNCATE ... RESTART IDENTITY CASCADE` antes de cada cenário.

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
