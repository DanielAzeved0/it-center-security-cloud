# DECISIONS.md

# Registro de Decisões Arquiteturais

## Objetivo

Documentar todas as decisões importantes tomadas durante o desenvolvimento do IT Center Security Cloud.

Este documento deve responder:

* O que foi decidido?
* Por que foi decidido?
* Quais alternativas existiam?
* Quais são os impactos da decisão?

---

# ADR-001

## Data

2026-06-24

## Decisão

O projeto será desenvolvido inicialmente como uma aplicação monolítica.

## Motivo

O objetivo do MVP é validar o produto rapidamente.

Microserviços aumentariam:

* Complexidade
* Custos
* Tempo de desenvolvimento
* Tempo de manutenção

## Alternativas Avaliadas

* Microserviços
* Arquitetura distribuída

## Resultado

Aplicação monolítica.

---

# ADR-002

## Data

2026-06-24

## Decisão

Utilizar Oracle Cloud Free Tier como ambiente principal.

## Motivo

Permite:

* Hospedagem gratuita
* Docker
* Banco PostgreSQL
* HTTPS
* Portfólio profissional

## Alternativas Avaliadas

* AWS
* Azure
* Google Cloud
* VPS paga

## Resultado

Oracle Cloud Free Tier.

---

# ADR-003

## Data

2026-06-24

## Decisão

Utilizar FastAPI como backend principal.

## Motivo

* Simples
* Moderno
* Excelente documentação
* Ótima integração com PostgreSQL
* Muito rápido para MVP

## Alternativas Avaliadas

* ASP.NET Core
* Express.js
* NestJS
* Django

## Resultado

FastAPI.

---

# ADR-004

## Data

2026-06-24

## Decisão

Utilizar PostgreSQL como banco de dados oficial.

## Motivo

* Open Source
* Gratuito
* Escalável
* Compatível com SaaS futuro

## Alternativas Avaliadas

* SQLite
* MySQL
* MariaDB

## Resultado

PostgreSQL.

---

# ADR-005

## Data

2026-06-24

## Decisão

Utilizar PowerShell como agente Windows.

## Motivo

* Presente em praticamente todos os Windows
* Não exige instalação adicional
* Fácil distribuição
* Ideal para ambientes corporativos

## Alternativas Avaliadas

* Python Agent
* C# Agent
* Go Agent

## Resultado

PowerShell.

---

# ADR-006

## Data

2026-06-24

## Decisão

Utilizar Next.js para o Dashboard.

## Motivo

* Moderno
* Excelente para dashboards
* Permite futura evolução para SaaS

## Alternativas Avaliadas

* React puro
* Angular
* Vue

## Resultado

Next.js.

---

# ADR-007

## Data

2026-06-24

## Decisão

Utilizar Docker e Docker Compose desde o início.

## Motivo

* Facilita deploy
* Facilita migração
* Padroniza ambiente

## Alternativas Avaliadas

* Instalação manual
* Scripts Shell

## Resultado

Docker Compose.

---

# ADR-008

## Data

2026-06-24

## Decisão

Implementar funcionalidades de SOC de forma gradual.

## Motivo

O objetivo principal do MVP é:

* Inventário
* Monitoramento
* Observabilidade

SOC avançado será implementado em etapas.

## Alternativas Avaliadas

* Wazuh desde o início
* SIEM completo desde o início

## Resultado

SOC Light no MVP.

---

# ADR-009

## Data

2026-06-24

## Decisão

Utilizar ASSET_POLICY.md como fonte de verdade para validação de softwares autorizados.

## Motivo

Evitar falsos positivos.

Exemplo:

RustDesk é utilizado legitimamente pela equipe de TI.

## Alternativas Avaliadas

* Lista fixa de softwares proibidos
* Regras rígidas sem contexto

## Resultado

Validação baseada em política.

---

# ADR-010

## Data

2026-06-24

## Decisão

O sistema não irá coletar dados pessoais ou conteúdo de usuários.

## Motivo

Respeitar privacidade.

Evitar riscos legais.

## Não será coletado

* Senhas
* Cookies
* Histórico de navegação
* Arquivos pessoais
* Conteúdo de documentos
* E-mails

## Resultado

Coleta apenas operacional.

---

# ADR-011

## Data

2026-06-24

## Decisão

Toda nova funcionalidade deverá possuir documentação antes da implementação.

## Motivo

Evitar retrabalho.

Garantir padronização.

Facilitar manutenção.

## Resultado

Fluxo obrigatório:

Planejamento
↓
Documentação
↓
Implementação
↓
Teste
↓
Deploy

---

# ADR-012

## Data

2026-06-24

## Decisão

O repositório permanecerá privado durante o desenvolvimento inicial.

## Motivo

* Evitar exposição de código incompleto
* Evitar vazamento de informações internas
* Permitir mudanças arquiteturais sem impacto

## Critério para Tornar Público

* MVP concluído
* Documentação concluída
* Secrets removidos
* Dados corporativos removidos

## Resultado

Repositório privado inicialmente.

---

# Modelo para Novas Decisões

## ADR-XXX

### Data

YYYY-MM-DD

### Decisão

Descrição da decisão.

### Motivo

Justificativa.

### Alternativas Avaliadas

Lista de alternativas.

### Resultado

Decisão final.
