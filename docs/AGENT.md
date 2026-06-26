# AGENT.md

# IT Center Security Cloud - Agente Windows

## Objetivo

O agente Windows é responsável por coletar informações da máquina local e enviá-las para a API central do IT Center Security Cloud.

O agente deve ser:

* Leve
* Seguro
* Simples
* Autônomo
* Compatível com Windows 10 e Windows 11

---

# Responsabilidades

O agente deve:

* Coletar informações da máquina
* Coletar métricas
* Coletar eventos de segurança
* Enviar dados para a API
* Operar mesmo sem conexão temporária

---

# Dados Coletados

## Inventário

* Hostname
* Usuário logado
* Endereço IP
* Sistema Operacional
* Versão do Windows
* CPU
* Memória RAM
* Disco

---

## Monitoramento

* Uso de CPU
* Uso de RAM
* Uso de Disco
* Uptime

---

## Segurança

* Firewall habilitado
* Defender habilitado
* RDP habilitado
* Usuários administradores locais
* Dispositivos USB
* Softwares instalados

---

# Dados Proibidos

O agente nunca deverá coletar:

* Senhas
* Cookies
* Histórico de navegação
* Conteúdo de documentos
* Arquivos pessoais
* E-mails

---

# Frequência de Coleta

Métricas:

5 minutos

Inventário:

24 horas

Segurança:

15 minutos

---

# Estrutura

agent-windows/

* itcenter-agent.ps1
* config.json
* cache/
* logs/

---

# Fluxo

Coletar dados
↓
Gerar JSON
↓
Enviar API
↓
Receber resposta
↓
Registrar log

---

# Estado Atual da Implementação

O agente PowerShell já possui as primeiras coletas locais do EPIC 4.

## Coletas implementadas

```text
Hostname
Usuário em execução
IPv4 local
Sistema operacional
Programas instalados
Uso de CPU
Uso de RAM
Uso de disco
Uptime em segundos
JSON de check-in
```

## JSON atual

O JSON gerado deve seguir o contrato do endpoint:

```text
POST /api/v1/agent/checkin
```

Campos gerados:

```text
hostname
username
ip_address
operating_system
os_version
cpu_usage
ram_usage
disk_usage
uptime_seconds
installed_programs
security
```

Observações:

* `installed_programs` agora é preenchido com o snapshot local dos programas instalados.
* O bloco `security` usa coletas reais do EPIC 6 para Firewall, Defender, RDP, administradores locais, USB e falhas de login.
* O agente já envia o check-in para `POST /api/v1/agent/checkin`.
* O JSON do check-in é enviado como bytes UTF-8 para suportar nomes de programas com acentos e caracteres especiais.
* Se a API falhar, o agente registra aviso e salva o JSON em `agent-windows/cache`.
* No próximo ciclo, o agente tenta reenviar check-ins pendentes antes de enviar a coleta atual.
* O agente já registra as coletas em `agent-windows/logs/itcenter-agent.log`.

## Testes atuais

Os testes do agente ficam em:

```text
agent-windows/tests/run-agent-tests.ps1
```

Eles validam:

```text
CPU entre 0 e 100
RAM entre 0 e 100
Disco entre 0 e 100
Payload com campos obrigatórios
JSON válido e parseável
Requisicao POST com header X-Agent-Api-Key
Body JSON enviado para /api/v1/agent/checkin
Cache offline em arquivo JSON
Reenvio de check-ins pendentes
Coletas de seguranca do EPIC 6
```

---

# Cache Offline

Caso a API esteja indisponível:

* Salvar dados localmente
* Reenviar posteriormente

---

# Critério de Sucesso

O agente estará concluído quando:

* Conseguir coletar dados
* Gerar JSON válido
* Enviar para API
* Operar offline temporariamente

---

# EPIC 6 - Coletas de Seguranca Implementadas

Coletas implementadas:

```text
Firewall habilitado
Windows Defender habilitado
RDP habilitado
Administradores locais
Dispositivos USB de armazenamento
Falhas de login na ultima hora
```

Campos enviados no bloco `security`:

```text
firewall_enabled
defender_enabled
rdp_enabled
local_admins
usb_devices
failed_logins_last_hour
```

Estado atual:

* `firewall_enabled` e coletado por `Get-NetFirewallProfile`.
* `defender_enabled` e coletado por `Get-MpComputerStatus`.
* `rdp_enabled` e coletado no registro `HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server`.
* `local_admins` e coletado pelo grupo local de administradores via SID `S-1-5-32-544`.
* `usb_devices` coleta metadados tecnicos de discos USB, sem ler conteudo de arquivos.
* `failed_logins_last_hour` conta eventos 4625 no log Security da ultima hora; se o log nao estiver acessivel, retorna 0.
* Os testes do agente validam as coletas do EPIC 6.
