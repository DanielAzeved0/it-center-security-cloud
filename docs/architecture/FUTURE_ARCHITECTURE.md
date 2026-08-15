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
* Criar servico Windows — item generico (para a coleta em si, via Service Control Manager) segue sem decisao; resolvido parcialmente apenas para o caso de atualizacao automatica, ver item abaixo.
* Adicionar atualizacao automatica — em planejamento real (ADR-032, EPIC 22): updater dedicado (`itcenter-agent-updater.ps1`) 100% PowerShell puro, com Tarefa Agendada propria de frequencia menor que o check-in, sem Servico Windows nativo via SCM e sem NSSM/WinSW (ver ADR-005, ADR-025). Ainda sem codigo.
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

Concluido (EPIC 12, ADR-021/ADR-022):

* Login no dashboard (Bearer token HMAC SHA-256).
* Usuarios administrativos (`users`) com perfis e permissoes (`admin`/`analyst`/`viewer`).
* Auditoria de acoes sensiveis (`audit_logs`: login, falha de login, logout, resolucao de alerta).

Entregas recomendadas restantes:

* Evoluir `AGENT_API_KEY` global para credenciais por agente ou por tenant.
* Permitir rotacao e revogacao de credenciais do agente.
* Reavaliar a necessidade do Basic Auth do Nginx agora que o login administrativo esta em producao (ADR-023).

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

### Fase F - Observabilidade — implementada (ADR-030, EPIC 21, 2026-08-15), ativacao em producao pendente

Meta:

Adicionar visibilidade operacional da **infraestrutura** (Edge Node e containers) sem mudar o contrato atual da aplicacao e sem duplicar a coleta de metricas por maquina que o agente Windows ja faz (`metrics`, EPIC 3; retencao planejada na Fase E acima).

Entregas recomendadas:

* Manter logs em `stdout` e `stderr`.
* [x] `node_exporter` para metricas de host (CPU/RAM/disco/rede da VM) e cAdvisor para saude dos containers — implementados em `infra/docker-compose.production.yml` sob `profiles: ["observability"]`.
* [x] Prometheus com scrape config apontando para essas duas fontes; Grafana com dashboard pre-configurado para saude do Edge Node (`infra/observability/`) — nenhum dos dois exposto publicamente (Nginx continua unico ponto de entrada; acesso via `docker exec`/tunel SSH, ver `docs/architecture/NETWORK.md`).
* [ ] Adicionar Loki ou Promtail para logs centralizados — nao implementado nesta rodada.
* [ ] Criar alertas para containers unhealthy — nao implementado nesta rodada.
* [ ] Criar alertas para disco baixo e memoria baixa — nao implementado nesta rodada.
* [ ] Criar alerta para certificado perto do vencimento — nao implementado nesta rodada.
* [ ] Criar alerta para falha de backup — nao implementado nesta rodada.
* [ ] Registrar metricas de latencia da API e volume de check-ins/eventos (comportamento da plataforma, nao substitui `metrics` por maquina) — nao implementado nesta rodada.
* [ ] Validar impacto de recursos no free tier (`infra/scripts/ops-check.sh`) antes de ativar em producao — pendente de execucao manual em `itcenter-edge-01`, deliberadamente nao simulada (ver `docs/development/TASKS.md` e `docs/deployment/DEPLOYMENT_HISTORY.md`, 2026-08-15).

Resultado esperado:

Capacidade de diagnosticar incidentes mais rapido sem aumentar demais a complexidade do MVP, e sem duplicar responsabilidade com o pipeline de metricas do agente.

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

### Fase H - Hub de integracao com ferramentas open source — RustDesk implementado (EPIC 19, concluida em 2026-08-04)

Meta:

O IT Center nao deve substituir ferramentas maduras e consolidadas do mercado. Em vez disso, deve atuar como uma plataforma central (hub) que integra solucoes open source especialistas via API REST, autenticacao por token e Webhooks quando disponiveis, mantendo uma interface unica para operadores, tecnicos e administradores. Cada ferramenta externa continua responsavel pelo seu dominio de especialidade; o IT Center nao duplica esse papel.

Ferramentas avaliadas:

* **Snipe-IT** (ITAM — gestao de ativos) — implementado e **revertido em 2026-08-11** (ADR-028 -> ADR-033, EPIC 19): a integracao chegou a ir para producao (codigo + testes), mas nunca existiu um Snipe-IT real conectado (`SNIPEIT_BASE_URL` nunca configurado), sem necessidade concreta de ITAM identificada. Codigo, testes e a coluna `machines.snipeit_asset_id` foram removidos. Volta a ser aspiracional (registrado em EPIC 14) — revisitar apenas se surgir necessidade real, decidindo tambem onde hospedar um Snipe-IT de verdade.
* **RustDesk** — implementado (ADR-027, EPIC 19, concluida em 2026-08-04): acesso remoto seguro entre tecnico e equipamento (open source, com opcao de auto-hospedagem, ja reconhecido em `docs/security/ASSET_POLICY.md`). O IT Center armazena o ID do RustDesk de cada equipamento e permite iniciar uma sessao remota com um clique associado ao ativo correspondente. Extensao planejada (ADR-034, EPIC 23): o agente tenta detectar automaticamente esse ID lendo a configuracao local do RustDesk ja instalado, mantendo o cadastro manual sempre disponivel como alternativa/fallback.
* **NetBox** — ainda aspiracional (sem ADR/EPIC): source of truth da infraestrutura (data centers, racks, switches, roteadores, firewalls, VLANs, redes, prefixos, IPAM, conexoes fisicas, topologia). O IT Center consultaria dispositivos cadastrados, exibiria IPs/VLANs e relacionaria equipamentos aos ativos, sem duplicar o papel de source of truth do NetBox. Valor real depende do projeto operar em ambientes com infraestrutura de rede propria a gerenciar (racks, switches) — nao e o caso do MVP atual (uma unica VM).

Observabilidade (Prometheus + Grafana) saiu desta lista: o escopo correto para essas duas ferramentas e a **infraestrutura** do proprio IT Center (Edge Node/containers), nao um dominio por-ativo como os tres acima — ver Fase F (Observabilidade), ADR-030 e EPIC 21.

Modelo de integracao (padrao comum as ferramentas do hub):

```text
Projeto Externo -> API REST -> Integration Service -> Banco do IT Center -> Frontend
```

Entregas recomendadas:

* Consumir a API REST de cada ferramenta com autenticacao por token; usar Webhooks quando a ferramenta oferecer.
* Implementar cada integracao como um servico desacoplado (Integration Service), que pode ser ativado, desativado ou substituido sem impactar o restante da plataforma.
* Armazenar no banco do IT Center apenas o necessario para consulta rapida e relacionamento interno (ex.: ID do host no RustDesk), evitando duplicar dados que ja tem fonte oficial externa.
* Botao de acesso remoto por ativo integrado ao RustDesk.
* Consulta de infraestrutura de rede (IPs, VLANs, topologia) via NetBox associada ao ativo correspondente, quando/se essa integracao avancar.

Resultado esperado:

Experiencia unificada para o operador — RustDesk para acesso remoto no curto prazo; Snipe-IT (ITAM) e NetBox (infraestrutura/IPAM/topologia) como fontes de inventario especializado se e quando o projeto operar em contextos que justifiquem — sem o IT Center assumir a responsabilidade tecnica de nenhuma dessas especialidades.

## Ordem recomendada

```text
1. Estabilizar MVP (concluido)
2. Adicionar autenticacao e auditoria (concluido, EPIC 12)
3. Profissionalizar agente Windows (concluido, EPIC 16, incluindo assinatura de codigo via ADR-031)
4. Transformar regras SOC em politicas configuraveis
5. Criar estrategia de retencao e agregacao de dados
6. Adicionar observabilidade de infraestrutura (Prometheus + Grafana, ADR-030, EPIC 21)
7. Separar servicos somente quando a carga justificar
8. Hub de integracao: RustDesk (concluido, ADR-027, EPIC 19) e relatorios/dashboard executivo (concluido, ADR-029, EPIC 20); Snipe-IT revertido (ADR-028 -> ADR-033) e NetBox somente se o projeto operar em contexto que justifique
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
