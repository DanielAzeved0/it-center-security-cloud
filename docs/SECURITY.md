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

* API Key

Futuro:

* JWT
* RBAC

---

## Proteção do Banco

* Acesso apenas interno
* Sem exposição pública
* Backups automáticos

---

## Segurança do Agente

* Comunicação HTTPS
* API Key obrigatória
* Validação de payload

---

## Segurança do Dashboard

* Login obrigatório
* Sessões expiram
* Controle de acesso

---

# Requisitos Obrigatórios

Não serão aceitos:

* Senhas em texto plano
* Secrets no GitHub
* Banco exposto na internet
* HTTP sem TLS
