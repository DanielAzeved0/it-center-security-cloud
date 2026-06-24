# CONTRIBUTING.md

# Guia de Contribuição

## Objetivo

Este documento define as regras de contribuição para o projeto IT Center Security Cloud.

Aplica-se a:

* Desenvolvedores humanos
* Agentes de IA
* Codex
* Cursor
* Claude Code
* Ferramentas de automação

---

# Filosofia do Projeto

O projeto foi criado seguindo cinco princípios fundamentais:

1. Simplicidade
2. Segurança
3. Baixo custo
4. Manutenibilidade
5. Escalabilidade futura

Toda contribuição deve respeitar esses princípios.

---

# Fluxo Obrigatório

Nenhuma funcionalidade deve ser implementada sem seguir o fluxo abaixo.

```text
Planejamento
    ↓
Documentação
    ↓
Implementação
    ↓
Teste
    ↓
Deploy
```

É proibido pular etapas.

---

# Documentação Obrigatória

Antes de escrever código, consulte:

* PROJECT_PLAN.md
* ARCHITECTURE.md
* DATABASE.md
* API.md
* AGENT.md
* SECURITY.md
* SOC_RULES.md
* ASSET_POLICY.md
* DECISIONS.md
* TASKS.md
* ROADMAP.md

---

# Fonte da Verdade

Cada assunto possui um documento responsável.

## Arquitetura

Responsável:

ARCHITECTURE.md

---

## Banco de Dados

Responsável:

DATABASE.md

---

## API

Responsável:

API.md

---

## Segurança

Responsável:

SECURITY.md

---

## Regras SOC

Responsável:

SOC_RULES.md

---

## Políticas de Ativos

Responsável:

ASSET_POLICY.md

---

## Planejamento

Responsável:

PROJECT_PLAN.md

---

# Regras para Desenvolvedores

## Não adicionar tecnologias sem justificativa

Antes de adicionar uma nova tecnologia:

1. Registrar em DECISIONS.md
2. Justificar a escolha
3. Comparar alternativas

---

## Não criar tabelas fora do DATABASE.md

Toda alteração de banco deve ser documentada primeiro.

---

## Não criar endpoints fora do API.md

Toda alteração na API deve ser documentada primeiro.

---

## Não alterar arquitetura sem aprovação

Mudanças estruturais devem ser registradas em:

DECISIONS.md

---

# Stack Oficial

## Backend

* Python
* FastAPI

---

## Banco

* PostgreSQL

---

## Frontend

* Next.js
* TypeScript

---

## Infraestrutura

* Docker
* Docker Compose
* Nginx

---

## Agente

* PowerShell

---

# Tecnologias Não Permitidas no MVP

Não utilizar:

* Kubernetes
* RabbitMQ
* Kafka
* Redis
* Microserviços
* Elasticsearch

A menos que exista uma decisão formal registrada em DECISIONS.md.

---

# Segurança

É proibido:

* Commitar senhas
* Commitar tokens
* Commitar chaves privadas
* Commitar arquivos .env

---

# Arquivos Sensíveis

Adicionar ao .gitignore:

```text
.env
.env.local
.env.production
*.key
*.pem
```

---

# Commits

Utilizar padrão:

```text
feat: nova funcionalidade

fix: correção

docs: documentação

refactor: refatoração

test: testes

infra: infraestrutura
```

Exemplos:

```text
feat: create machine checkin endpoint

docs: update architecture document

fix: correct machine status calculation
```

---

# Pull Requests

Todo Pull Request deve responder:

## O que foi alterado?

## Por que foi alterado?

## Existe impacto na arquitetura?

## Existe impacto no banco?

## Existe impacto na API?

---

# Regras para Agentes de IA

Antes de implementar qualquer funcionalidade:

1. Ler PROJECT_PLAN.md
2. Ler ARCHITECTURE.md
3. Ler DATABASE.md
4. Ler API.md
5. Ler DECISIONS.md

---

# Agentes Não Devem

* Inventar endpoints
* Inventar tabelas
* Alterar arquitetura sem registro
* Adicionar tecnologias fora da stack oficial

---

# Agentes Devem

* Seguir TASKS.md
* Seguir ROADMAP.md
* Atualizar documentação quando necessário
* Gerar código simples
* Priorizar clareza

---

# Definição de Pronto

Uma tarefa será considerada concluída quando:

* Código implementado
* Código testado
* Documentação atualizada
* Sem erros conhecidos
* Commit realizado

---

# Objetivo Final

Construir uma plataforma de monitoramento, inventário e segurança que seja:

* Simples de operar
* Gratuita para iniciar
* Escalável para SaaS
* Útil para ambientes corporativos
* Valiosa para aprendizado de Infraestrutura, DevOps e Cyber Security

Toda contribuição deve aproximar o projeto desse objetivo.
