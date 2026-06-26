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

---

# ADR-013

## Data

2026-06-24

## Decisão

Integrar a API FastAPI diretamente ao PostgreSQL usando o driver psycopg.

## Motivo

O projeto já concluiu a criação do banco e das tabelas iniciais.

Manter repositórios em memória impediria o MVP de cumprir o critério de sucesso:

* A API salvar dados.
* O PostgreSQL armazenar dados.
* O dashboard consultar dados persistidos futuramente.

## Alternativas Avaliadas

* Continuar com repositórios em memória temporários.
* Usar SQLAlchemy desde o início.
* Usar psycopg diretamente.

## Resultado

Usar psycopg diretamente no MVP.

Impactos:

* Menos dependências e menor complexidade inicial.
* Queries SQL explícitas e alinhadas ao DATABASE.md.
* Possibilidade de migrar para SQLAlchemy futuramente se o domínio crescer.

---

# ADR-014

## Data

2026-06-25

## Decisão

Rodar o ambiente local completo com Docker Compose, incluindo PostgreSQL, backend FastAPI e frontend Next.js.

O backend deverá aplicar as migrations automaticamente antes de iniciar a API quando executado em container.

## Motivo

Durante a execução local, rodar banco, migration, backend e dashboard manualmente gerou atrito e erros de ambiente, como:

* `psql` ausente no Windows.
* `python` sem alias no CMD.
* backend desligado enquanto o dashboard tentava consumir a API.
* necessidade de lembrar a ordem correta de inicialização.

O Compose reduz esse atrito e mantém o fluxo coerente com a stack oficial já aprovada no ADR-007.

## Alternativas Avaliadas

* Continuar com execução manual de cada serviço.
* Criar scripts `.cmd` locais.
* Rodar apenas o PostgreSQL em Docker.
* Rodar PostgreSQL, backend e frontend em Docker Compose.

## Resultado

Usar `infra/docker-compose.yml` como entrada principal para desenvolvimento local integrado.

Comando oficial local:

```powershell
docker compose -f infra/docker-compose.yml up --build
```

Impactos:

* Menos dependência de Python, Node e psql instalados no host.
* Migrations aplicadas de forma previsível no startup do backend.
* Dashboard aponta para o backend pelo DNS interno `backend`.
* Nginx continua reservado para produção/cloud, não para o fluxo local inicial.

---

# ADR-015

## Data

2026-06-25

## Decisao

Adotar Docker Scout como gate de seguranca para imagens locais e tratar vulnerabilidades critical/high antes de publicar o ambiente.

O backend passa a usar `python:3.14-alpine`.

O frontend passa a usar Next.js `16.2.9`, `picomatch` `4.0.4` fixo e um patch de build para substituir o `picomatch` compilado dentro do Next quando necessario.

A imagem final do frontend remove o `npm` global e inicia o Next.js diretamente com `node`, porque o Docker Scout detectava `picomatch 4.0.3` dentro das dependencias internas do npm empacotado pela imagem base `node:22-alpine`.

O PostgreSQL permanece em `postgres:16-alpine`, com risco residual documentado quando a CVE vier da imagem oficial e ainda nao houver tag corrigida.

## Motivo

As varreduras iniciais apontaram:

* `infra-backend:latest` com CVEs critical/high vindas da base Debian.
* `infra-frontend:latest` com CVEs high em Next.js e `picomatch`.
* `postgres:16-alpine` com CVE residual em pacote da imagem oficial.

Como o produto e de seguranca, imagens com vulnerabilidades corrigiveis nao devem ser normalizadas no fluxo de desenvolvimento.

## Alternativas Avaliadas

* Ignorar alertas ate o deploy em cloud.
* Usar `npm audit fix --force`.
* Trocar backend para base Alpine.
* Atualizar dependencias diretas e documentar risco residual de imagem oficial.

## Resultado

* Backend migrou para Alpine e deve ficar sem critical/high no Scout.
* Frontend atualizou Next.js e corrige `picomatch` no build.
* Frontend remove `npm` global da imagem final para eliminar dependencias de build/runtime nao usadas.
* `npm audit fix --force` nao sera usado sem revisao.
* CVE residual de imagem oficial sera acompanhada como P1 e registrada em `docs/SECURITY.md`.

Impactos:

* Build fica mais rigoroso.
* O patch do frontend deve ser removido futuramente quando o Next empacotar `picomatch` corrigido diretamente.
* O deploy externo passa a depender do gate de imagens descrito em `docs/DEPLOYMENT.md`.

---

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
