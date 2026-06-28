# Evolucao arquitetural futura

Este documento registra as ideias e diretrizes arquiteturais para a evolucao futura do IT Center Security Cloud.

O objetivo e manter uma visao clara de crescimento sem antecipar complexidade desnecessaria. A arquitetura atual deve continuar simples, operavel e barata enquanto o MVP ainda esta sendo validado.

## Contexto

O projeto hoje esta estruturado como uma plataforma full stack de monitoramento, inventario e seguranca para maquinas Windows.

A arquitetura atual usa:

```text
Windows Agent
    |
    v
Nginx HTTPS
    |
    |-- Next.js Dashboard
    |
    `-- FastAPI Backend
            |
            v
        PostgreSQL
```

Em producao, os servicos rodam em Docker Compose no Edge Node da Oracle Cloud. Somente o Nginx expoe portas publicas. Backend, frontend e PostgreSQL permanecem isolados na rede Docker `itcenter-network`.

Essa arquitetura e adequada para o estagio atual do projeto.

## Diretriz principal

A diretriz tecnica para os proximos ciclos e:

```text
Fortalecer o monolito modular antes de distribuir a arquitetura.
```

Isso significa que o projeto nao deve migrar para microservicos, Kubernetes, filas ou arquitetura distribuida antes de existir uma necessidade real medida em producao.

O foco deve ser:

* melhorar confiabilidade;
* profissionalizar o agente Windows;
* fortalecer autenticacao e auditoria;
* tornar regras SOC configuraveis;
* controlar crescimento dos dados;
* adicionar observabilidade;
* separar servicos somente quando a carga justificar.

## O que nao fazer agora

No estagio atual, nao e recomendado:

* migrar para Kubernetes;
* dividir o backend em microservicos;
* adicionar broker de fila sem necessidade clara;
* criar multiplas VMs antes do MVP exigir;
* adicionar service mesh;
* substituir PostgreSQL sem motivo tecnico forte;
* criar uma plataforma SaaS completa antes de estabilizar o agente.

Essas tecnologias podem ser avaliadas no futuro, mas neste momento aumentariam custo, superficie de falha e esforco operacional.

## Plano de evolucao

### Fase A - Estabilizacao do MVP

Meta:

Consolidar o ambiente atual como uma base confiavel de producao.

Entregas recomendadas:

* Manter Docker Compose como orquestrador oficial do MVP.
* Validar preflight antes de cada deploy.
* Testar backup e restore periodicamente.
* Manter somente o Nginx exposto publicamente.
* Garantir que backend, frontend e PostgreSQL continuem isolados na rede Docker.
* Melhorar higiene do repositorio removendo artefatos locais de build, cache e logs quando aparecerem fora do `.gitignore`.
* Manter documentacao operacional atualizada a cada mudanca de infraestrutura.

Resultado esperado:

Ambiente reproduzivel, seguro o suficiente para o MVP e simples de operar.

### Fase B - Agente Windows como produto

Meta:

Transformar o agente Windows em um componente independente, instalavel e operavel em maquinas reais.

Entregas recomendadas:

* Separar o agente como produto com ciclo de versao proprio.
* Criar instalador.
* Criar servico Windows.
* Adicionar atualizacao automatica.
* Melhorar cache offline.
* Adicionar retry inteligente.
* Adicionar compressao de payloads quando necessario.
* Adicionar assinatura dos payloads.
* Adicionar identidade individual por agente.
* Permitir revogacao de agentes comprometidos.
* Expandir inventario, metricas e eventos do Windows.

Resultado esperado:

Agente confiavel, recuperavel em falhas de rede e pronto para ambientes reais.

### Fase C - Identidade e autenticacao

Meta:

Substituir controles temporarios de MVP por controles de identidade mais fortes.

Entregas recomendadas:

* Manter Basic Auth apenas como protecao simples de borda enquanto nao houver login de aplicacao.
* Implementar login no dashboard.
* Adicionar usuarios administrativos.
* Criar perfis e permissoes.
* Registrar auditoria de acoes sensiveis.
* Evoluir `AGENT_API_KEY` global para credenciais por agente ou por tenant.
* Permitir rotacao e revogacao de credenciais.

Resultado esperado:

Controle operacional melhor, menor impacto em caso de vazamento de uma credencial e base preparada para multiusuario.

### Fase D - Policy engine SOC

Meta:

Remover regras SOC hardcoded do backend e transformar deteccoes em politicas configuraveis.

Entregas recomendadas:

* Criar tabelas para politicas de seguranca.
* Permitir allowlists por ambiente, cliente ou grupo de maquinas.
* Versionar regras SOC.
* Permitir severidade configuravel.
* Registrar qual regra gerou cada evento ou alerta.
* Separar deteccao, avaliacao de politica e criacao de alerta em camadas claras.
* Manter regras simples antes de introduzir motor complexo de correlacao.

Resultado esperado:

Menos falso positivo, mais flexibilidade operacional e base preparada para SOC avancado.

### Fase E - Ciclo de vida dos dados

Meta:

Controlar crescimento do PostgreSQL sem perder informacao operacional importante.

Entregas recomendadas:

* Definir retencao para metricas brutas.
* Criar agregacoes por hora ou por dia quando houver volume.
* Avaliar particionamento da tabela `metrics` quando necessario.
* Manter backups compactados com retencao clara.
* Testar restore como parte do processo operacional.
* Documentar politica de dados sensiveis e dados nao coletados.

Resultado esperado:

Banco previsivel, menor risco de crescimento descontrolado e operacao mais simples.

### Fase F - Observabilidade

Meta:

Adicionar visibilidade operacional sem mudar o contrato atual da aplicacao.

Entregas recomendadas:

* Manter logs em `stdout` e `stderr`.
* Adicionar dashboards de saude com Prometheus e Grafana quando houver necessidade real.
* Adicionar Loki ou Promtail para logs centralizados.
* Criar alertas para containers unhealthy.
* Criar alertas para disco baixo e memoria baixa.
* Criar alerta para certificado perto do vencimento.
* Criar alerta para falha de backup.
* Registrar metricas de check-in do agente, latencia da API e volume de eventos.

Resultado esperado:

Capacidade de diagnosticar incidentes mais rapido sem aumentar demais a complexidade do MVP.

### Fase G - Escala e separacao de servicos

Meta:

Separar componentes somente quando houver necessidade comprovada.

Gatilhos para evolucao:

* Muitos agentes gerando carga constante.
* Banco crescendo acima da capacidade do Edge Node.
* Necessidade de alta disponibilidade.
* Necessidade de isolar clientes.
* Tempo de resposta da API degradado.
* Deploys impactando operacao.

Possiveis evolucoes:

* Mover PostgreSQL para instancia privada ou servico gerenciado.
* Manter Nginx como ponto de entrada.
* Separar backend e banco em subnet privada.
* Adicionar fila apenas para tarefas lentas, retry ou efeitos externos.
* Avaliar Kubernetes somente quando Docker Compose deixar de atender os requisitos reais.

Resultado esperado:

Escala com justificativa tecnica, sem overengineering antecipado.

## Ordem recomendada

```text
1. Estabilizar MVP
2. Profissionalizar agente Windows
3. Adicionar autenticacao e auditoria
4. Transformar regras SOC em politicas configuraveis
5. Criar estrategia de retencao e agregacao de dados
6. Adicionar observabilidade
7. Separar servicos somente quando a carga justificar
```

## Principios de decisao

* Preferir solucao simples e operavel.
* Nao distribuir a arquitetura antes de medir necessidade.
* Proteger a borda com Nginx e HTTPS obrigatorio.
* Manter PostgreSQL como fonte de verdade.
* Tratar agente Windows como produto critico.
* Automatizar deploy, backup, restore e preflight.
* Documentar antes de implementar mudancas estruturais.

## Criterios para reavaliar a arquitetura

A arquitetura deve ser reavaliada quando pelo menos um destes sinais aparecer:

* Edge Node com CPU ou memoria saturada de forma recorrente.
* PostgreSQL com crescimento rapido e impacto perceptivel.
* Backups demorando demais ou falhando com frequencia.
* Volume de check-ins exigindo processamento assincromo.
* Necessidade real de multiempresa.
* Necessidade de separar dados por cliente.
* Necessidade de alta disponibilidade.
* Deploys frequentes causando indisponibilidade.
* Operacao exigindo auditoria forte e trilhas de acesso.

Antes desses sinais, a melhor decisao continua sendo amadurecer a arquitetura atual.
