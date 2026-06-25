# SECURITY.md

# Política de Segurança

## Objetivo

Garantir que o IT Center Security Cloud seja desenvolvido seguindo princípios de segurança desde o início.

---

# Princípios

## Menor Privilégio

Cada componente deve possuir apenas as permissões necessárias.

---

## Criptografia

Todo tráfego externo deve utilizar HTTPS.

---

## Segredos

Nunca armazenar:

* Senhas
* Tokens
* Chaves

Dentro do código-fonte.

Utilizar:

.env

---

## Auditoria

Toda ação crítica deverá gerar logs.

---

## Proteção da API

MVP:

* API Key obrigatória para agentes
* Validação de payloads
* Erros sem detalhes internos

Futuro:

* JWT
* RBAC
* Rate limit
* Logs de auditoria completos

---

## Proteção do Banco

* Acesso apenas interno
* Sem exposição pública
* Backups automáticos

---

## Segurança do Agente

* Comunicação HTTPS
* API Key obrigatória
* Header oficial: X-Agent-Api-Key
* Validação de payload
* Cache offline sem dados sensíveis

---

## Segurança do Dashboard

MVP local/laboratório:

* Pode operar sem login apenas enquanto não estiver exposto na internet

Antes de exposição externa:

* Login obrigatório
* Sessões com expiração
* Controle de acesso

---

# Requisitos Obrigatórios

Não serão aceitos:

* Senhas em texto plano
* Secrets no GitHub
* Banco exposto na internet
* HTTP sem TLS
* Check-in de agente sem API Key
