# PROJECT_PLAN.md

# IT Center Security Cloud

## Visão do Projeto

O IT Center Security Cloud é uma plataforma de monitoramento, inventário, observabilidade e segurança para ambientes Windows.

O objetivo é fornecer uma solução simples, centralizada e de baixo custo para monitorar computadores, servidores e ativos corporativos.

O projeto será desenvolvido inicialmente para uso interno e aprendizado, podendo evoluir futuramente para uma solução SaaS.

---

# Problema que Estamos Resolvendo

Pequenas e médias empresas normalmente possuem:

* Pouca visibilidade sobre seus ativos
* Falta de inventário atualizado
* Falta de monitoramento centralizado
* Falta de alertas de segurança
* Dependência de ferramentas caras

O IT Center Security Cloud busca resolver esses problemas utilizando tecnologias gratuitas e open source.

---

# Objetivos do Projeto

## Objetivo Principal

Criar uma plataforma centralizada para:

* Inventário
* Monitoramento
* Observabilidade
* Segurança

---

## Objetivos Técnicos

Aprender e aplicar:

* Infraestrutura
* Cloud Computing
* DevOps
* Observabilidade
* Cyber Security
* Desenvolvimento Backend
* Desenvolvimento Frontend
* Docker
* PostgreSQL

---

## Objetivos Profissionais

Construir um projeto de portfólio capaz de demonstrar experiência prática em:

* Infraestrutura
* SOC
* Blue Team
* DevOps
* SRE

---

# Público-Alvo

## MVP

Uso próprio.

Laboratórios.

Pequenas empresas.

---

## Futuro

MSPs.

Consultorias de TI.

Empresas de pequeno e médio porte.

---

# Escopo do MVP

O MVP deverá possuir:

### Inventário

* Hostname
* Usuário
* Sistema Operacional
* Programas Instalados

---

### Monitoramento

* CPU
* RAM
* Disco
* Uptime

---

### Dashboard

* Máquinas Online
* Máquinas Offline
* Último Check-in

---

### Segurança

* Firewall
* Defender
* USB
* RDP
* Administradores Locais

---

# Fora do Escopo do MVP

Não implementar neste momento:

* Multiempresa
* Multiusuário
* Billing
* Integrações complexas
* Kubernetes
* Microserviços
* SIEM completo
* Wazuh
* OpenVAS

Esses recursos serão avaliados futuramente.

Esta lista é sobre escopo de produto/funcionalidade (o que o MVP ainda não faz). A lista de tecnologias de infraestrutura proibidas no código (Kubernetes, RabbitMQ, Kafka, Redis, microsserviços, Elasticsearch) é uma categoria diferente e está em `docs/development/CONTRIBUTING.md` ("Tecnologias Não Permitidas no MVP") — as duas coexistem intencionalmente, não são a mesma lista desalinhada por acidente.

---

# Princípios do Projeto

## Custo Zero

Todo o MVP deve funcionar utilizando apenas recursos gratuitos.

---

## Simplicidade

Sempre escolher a solução mais simples possível.

---

## Segurança

Segurança deve ser considerada desde o início.

---

## Documentação

Nenhuma funcionalidade deve existir sem documentação.

---

## Escalabilidade

Mesmo simples, a arquitetura deve permitir crescimento futuro.

---

# Hospedagem

Ambiente oficial:

Oracle Cloud Free Tier

Objetivo:

Manter custo zero durante o desenvolvimento e MVP.

---

# Stack Oficial

Stack oficial completa e regras para adotar tecnologia nova estão em `docs/development/CONTRIBUTING.md` ("Stack Oficial").

Resumo: Python/FastAPI + PostgreSQL no backend, Next.js no frontend, PowerShell no agente, Docker/Docker Compose/Nginx na infraestrutura, mais Terraform para a camada de VCN/subnets/instância (ADR-024).

---

# Indicadores de Sucesso

O MVP será considerado bem-sucedido quando:

* O agente conseguir enviar dados.
* A API receber dados.
* O PostgreSQL armazenar dados.
* O dashboard exibir máquinas.
* O sistema gerar eventos de segurança básicos.
* O deploy estiver funcionando na Oracle Cloud.

---

# Visão de Longo Prazo

Transformar o IT Center Security Cloud em uma plataforma SaaS de monitoramento, inventário e segurança para pequenas e médias empresas.

A plataforma deverá manter uma versão gratuita para laboratórios, aprendizado e pequenas operações.

---

# Ver também

* `README.md` — visão técnica, arquitetura, stack, como executar e status resumido do projeto.
* `docs/development/ROADMAP.md` — fases, matriz de rastreabilidade e ADRs relacionados.
* `docs/development/TASKS.md` — backlog oficial, sempre atualizado.
