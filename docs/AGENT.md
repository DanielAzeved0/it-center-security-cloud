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
