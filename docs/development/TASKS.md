# TASKS.md

# Backlog Oficial

## Status

Legenda:

[ ] Não iniciado

[~] Em andamento

[x] Concluído

---

# EPIC 1 - Fundação do Projeto

Objetivo:

Criar a estrutura base do projeto.

### Tarefas

[x] Criar repositório GitHub

[x] Criar estrutura de diretórios

[x] Criar README.md

[x] Criar ROADMAP.md e TASKS.md

[x] Criar docs/architecture/ARCHITECTURE.md

[x] Criar docs/backend/DATABASE.md

[x] Criar docs/backend/API.md

[x] Criar docs/agent/CHECKIN.md

[x] Criar docs/security/SECURITY.md

[x] Criar docs/security/SOC_RULES.md

[x] Criar docs/security/ASSET_POLICY.md

[x] Criar docs/development/DECISIONS.md

---

# EPIC 2 - Backend

Objetivo:

Criar API funcional.

### Tarefas

[x] Criar projeto FastAPI

[x] Configurar ambiente Python

[x] Criar endpoint /health

[x] Criar endpoint /agent/checkin

[x] Criar endpoint /machines

[x] Criar endpoint /machines/{id}

[x] Criar endpoint /machines/{id}/metrics

[x] Criar endpoint /machines/{id}/programs

[x] Criar endpoint /alerts

[x] Criar endpoint /alerts/{id}/resolve

[x] Criar endpoint /security-events

---

# EPIC 3 - Banco

Objetivo:

Persistência de dados.

### Tarefas

[x] Criar PostgreSQL

[x] Criar Docker para PostgreSQL

[x] Criar tabela machines

[x] Criar tabela metrics

[x] Criar tabela installed_programs

[x] Criar tabela security_events

[x] Criar tabela alerts

[x] Criar tabela agent_configs

[x] Criar migrations

[x] Integrar API ao PostgreSQL

[x] Persistir check-in em machines, metrics e installed_programs

[x] Ler machines, alerts e security_events do PostgreSQL

[x] Persistir agent_configs

---

# EPIC 4 - Agente Windows

Objetivo:

Coleta de informações.

### Tarefas

[x] Criar estrutura do agente

[x] Criar config.json

[x] Coletar hostname

[x] Coletar usuário

[x] Coletar IP

[x] Coletar sistema operacional

[x] Coletar programas instalados

[x] Coletar uptime

[x] Coletar CPU

[x] Coletar RAM

[x] Coletar disco

[x] Gerar JSON

[x] Enviar para API

[x] Cache offline

[x] Reenviar dados em caso de falha

---

# EPIC 5 - Dashboard

Objetivo:

Visualização inicial.

### Tarefas

[x] Criar projeto Next.js

[x] Criar tela Dashboard

[x] Criar tela Máquinas

[x] Criar tela Alertas

[x] Criar tela Segurança

[x] Consumir API

---

# EPIC 6 - SOC Light

Objetivo:

Primeiras detecções.

### Tarefas

[x] Detectar Firewall

[x] Detectar Defender

[x] Detectar RDP

[x] Detectar USB

[x] Detectar Administradores Locais

[x] Detectar Ferramentas Remotas

[x] Gerar Eventos

[x] Gerar Alertas

---

# EPIC 7 - Produção

Objetivo:

Primeiro deploy.

### Tarefas

[x] Criar VM Oracle

[x] Instalar Docker

[x] Configurar PostgreSQL

[x] Configurar Nginx

[x] Configurar HTTPS

[x] Publicar Backend

[x] Publicar Frontend

---

# EPIC 8 - Agente Windows em Produção

Objetivo:

Transformar o agente PowerShell em um componente operacional, instalavel e validado contra o ambiente publicado.

### Tarefas

[x] Validar check-in do agente contra a URL publica de producao

[x] Validar envio do header X-Agent-Api-Key em producao

[x] Validar persistencia do primeiro check-in real no PostgreSQL

[x] Validar que a maquina aparece no dashboard publicado

[x] Criar script de instalacao do agente

[x] Criar script de desinstalacao do agente

[x] Registrar o agente como servico Windows ou tarefa agendada controlada

[x] Definir local padrao de instalacao no Windows

[x] Definir local padrao de logs do agente

[x] Definir local padrao de cache offline do agente

[x] Padronizar config.json do agente para producao

[x] Validar ciclo periodico de check-in

[x] Melhorar retry inteligente em falhas temporarias

[x] Garantir que cache offline nao armazene dados proibidos

[x] Documentar instalacao real em docs/agent/INSTALLATION.md

[x] Documentar troubleshooting do agente

---

# EPIC 9 - Validação do Fluxo Fim a Fim

Objetivo:

Provar o fluxo completo entre agente, Nginx, FastAPI, PostgreSQL e dashboard com dados reais.

Observacao de validacao:

Em 2026-06-29, `python -m pytest backend\tests\test_agent_checkin.py -q` passou com PostgreSQL local via Docker Compose: 9 testes aprovados. O teste `test_agent_checkin_persists_full_operational_snapshot` cobre a persistencia do snapshot operacional em `machines`, `metrics`, `installed_programs`, `machine_local_admins` e `agent_configs`, alem das rotas de leitura usadas pelo dashboard.

### Tarefas

[x] Executar check-in real a partir de uma maquina Windows

[x] Confirmar recebimento pelo Nginx em HTTPS

[x] Confirmar validacao de X-Agent-Api-Key no backend

[x] Confirmar gravacao em machines

[x] Confirmar gravacao em metrics

[x] Confirmar gravacao em installed_programs

[x] Confirmar sincronizacao de machine_local_admins

[x] Confirmar criacao de agent_configs no primeiro check-in

[x] Confirmar geracao de security_events

[x] Confirmar geracao de alerts quando houver risco

[x] Confirmar exibicao dos dados no dashboard

[x] Registrar evidencias do teste em docs/deployment/DEPLOYMENT_HISTORY.md

[x] Atualizar docs/deployment/KNOWN_ISSUES.md se houver falha conhecida

---

# EPIC 10 - Dashboard Operacional

Objetivo:

Evoluir o dashboard de visualizacao inicial para uma ferramenta de operacao diaria.

### Tarefas

[x] Melhorar tela de detalhes da maquina

[x] Exibir historico de metricas por maquina

[x] Exibir programas instalados por maquina

[x] Exibir administradores locais por maquina

[x] Exibir eventos de seguranca por maquina

[x] Permitir resolver alertas pela interface

[x] Adicionar filtros por severidade

[x] Adicionar filtros por tipo de evento

[x] Adicionar filtros por maquina

[x] Melhorar estados vazios quando nao houver agente

[x] Melhorar indicacao de maquina online e offline

[x] Validar responsividade das telas principais

[x] Atualizar docs/backend/API.md se novas chamadas forem necessarias

---

# EPIC 11 - SOC Light Pendências

Objetivo:

Concluir regras SOC ja definidas e preparar a politica para configuracao operacional.

### Tarefas

[x] Implementar regra unknown_asset

[x] Implementar regra machine_offline

[x] Definir criterio oficial de maquina conhecida

[x] Definir janela oficial para maquina offline

[x] Melhorar validacao de RDP autorizado por politica

[x] Melhorar validacao de ferramenta remota autorizada por politica

[x] Evitar duplicidade indevida de alertas abertos

[x] Criar testes para unknown_asset

[x] Criar testes para machine_offline

[x] Atualizar docs/security/SOC_RULES.md com o status das regras

[x] Atualizar docs/security/ASSET_POLICY.md se novas listas forem necessarias

---

# EPIC 12 - Governança e Autenticação

Objetivo:

Substituir controles minimos do MVP por autenticacao e governanca adequadas para uso administrativo.

### Tarefas

[x] Definir modelo de usuarios

[x] Definir modelo de permissoes

[x] Criar tabela users

[x] Criar tabela audit_logs

[x] Implementar login

[x] Implementar sessoes ou JWT

[x] Proteger rotas administrativas do backend

[x] Proteger paginas administrativas do dashboard

[x] Registrar auditoria de acoes criticas

[x] Planejar API Key por agente

[x] Atualizar docs/security/AUTH.md

[x] Registrar decisoes relevantes em docs/development/DECISIONS.md

---

# EPIC 13 - Operação e Segurança de Produção

Objetivo:

Reduzir risco operacional do ambiente publicado e preparar manutencao continua.

### Tarefas

[x] Automatizar backup periodico do PostgreSQL

[x] Testar restore em ambiente controlado

    Validado em 2026-07-28: backup fresco gerado
    (itcenter-postgres-20260728T180730Z.sql.gz) e restaurado com
    ITCENTER_RESTORE_CONFIRM=YES sh infra/scripts/restore.sh contra
    o banco de producao. Schema recriado, todas as tabelas restauradas
    com contagens de linhas consistentes com o backup, backend
    saudavel (/api/v1/health) e dashboard funcional apos o restore.

[x] Validar rollback de deploy

    Validado em 2026-07-28: backup executado antes do teste, rollback
    de c682c7e para f27d00c concluido com sucesso (containers
    rebuilded e saudaveis, volume postgres_data preservado sem
    reiniciar o Postgres), seguido de rollforward de volta para
    c682c7e com sucesso.

[x] Validar renovacao de certificado TLS

    Validado em 2026-07-28: simulacao (TLS_RENEW_DRY_RUN=1) concluiu
    "all simulated renewals succeeded"; renovacao real corretamente
    identificou que o certificado so expira em 2026-09-24 e nao
    tentou renovar (comportamento esperado do Certbot). Durante a
    validacao foi descoberta e corrigida a tag invalida da imagem
    certbot/certbot:v4.21.0 (INCIDENTE 021 em POSTMORTEMS.md).

[x] Monitorar uso de disco da VM

[x] Monitorar uso de memoria da VM

[x] Monitorar containers unhealthy

[x] Criar alerta para expiracao de certificado

[x] Executar Docker Scout antes de publicar imagens

[x] Criar CI automatico no GitHub Actions

[x] Declarar dependencia `httpx` para testes FastAPI/Starlette no CI

[x] Criar deploy manual de producao no GitHub Actions

[x] Concluir deploy de producao pelo GitHub Actions

    Validado em 2026-06-30:

    * secrets de SSH cadastrados no GitHub Actions;
    * erro de sintaxe do workflow `deploy-production.yml` corrigido;
    * dependencia `httpx` declarada para o `TestClient` do FastAPI/Starlette;
    * workflow `CI` validado com sucesso no GitHub Actions: backend tests, frontend build e compose validation;
    * workflow `Deploy Production` executado manualmente com sucesso;
    * backup PostgreSQL criado antes do deploy;
    * build de backend e frontend concluido;
    * containers `postgres`, `backend`, `frontend` e `nginx` saudaveis;
    * smoke tests de producao aprovados;
    * dashboard publicado validado sem bug visual reportado.

[x] Documentar rotina operacional semanal

[x] Atualizar docs/deployment/TROUBLESHOOTING.md com novos cenarios

[x] Atualizar docs/deployment/POSTMORTEMS.md quando houver incidente

    Feito em 2026-07-28 apos os INCIDENTES 018, 019 e 020 (perda de
    chave SSH, ausencia de admin em producao e loop de login por
    conflito Basic Auth/Bearer). Item permanece como pratica continua
    para qualquer incidente futuro, nao apenas um registro unico.

---

# EPIC 14 - Melhorias Futuras

Objetivo:

Registrar evolucoes de produto fora do escopo operacional imediato.

### Tarefas

[ ] Wazuh

[ ] OpenVAS

[ ] Multiempresa

[ ] Integracao Microsoft 365

[ ] Integracao Active Directory (avaliar depois; nao entrou no lote priorizado em 2026-08-03)

[ ] Vulnerability Management

[ ] Billing

[ ] SaaS

[ ] Hub de integracao com ferramentas open source maduras, em vez de substitui-las (arquitetura detalhada em docs/architecture/FUTURE_ARCHITECTURE.md, Fase H). RustDesk e Snipe-IT saíram daqui e ganharam plano concreto na EPIC 19; NetBox continua aspiracional.

[ ] Integracao NetBox (source of truth de infraestrutura de rede, IPAM e topologia)

[ ] Avaliar reescrita do agente Windows em Go (condicional, ver ADR-025 e EPIC 16)

---

# EPIC 15 - Infraestrutura como Codigo (Terraform)

Objetivo:

Provisionar e versionar a camada de infraestrutura Oracle Cloud (VCN, subnets, security list, instancia) via Terraform, importando os recursos ja existentes em producao sem destruir ou recriar nada.

### Tarefas

[x] Registrar ADR-024 em docs/development/DECISIONS.md

[x] Criar docs/architecture/IAC.md

[x] Referenciar IAC.md a partir de INFRASTRUCTURE.md e NETWORK.md

[x] Criar infra/terraform/README.md

[x] Atualizar .gitignore com artefatos de Terraform

[x] Criar usuario IAM dedicado terraform-provisioner com API key propria

    Criado manualmente no Console OCI (grupo TerraformProvisioners,
    usuario terraform-provisioner, API key gerada e salva fora do
    repositorio). Concluido em 2026-08-04.

[x] Definir policy de escopo minimo (compartment especifico)

    Redigida em infra/terraform/README.md: inspect all-resources,
    manage virtual-network-family, manage instance-family e use
    volume-family. Aplicada `in tenancy` (nao `in compartment <nome>`)
    porque o Edge Node vive no root compartment do tenancy
    (danielazevedo081205), que nao existe como compartment nomeado
    separado - sintaxe de policy da OCI exige `in tenancy` nesse caso.

[x] Descobrir e registrar shape, availability domain, regiao e compartment atuais

    Executado via oci CLI em 2026-08-04. Compartment = root do tenancy.
    Regiao sa-saopaulo-1. AD gIEb:SA-SAOPAULO-1-AD-1. Shape real da
    instancia e VM.Standard.E2.1.Micro (fixo, sem shape_config) - o
    exemplo antigo em terraform.tfvars.example citava VM.Standard.A1.Flex,
    corrigido.

[x] Verificar se o IP publico 147.15.78.220 e reservado ou efemero

    Confirmado via `oci network public-ip get`: lifetime EPHEMERAL,
    scope AVAILABILITY_DOMAIN. Decisao registrada: manter efemero por
    ora (nenhum terraform apply de recriacao roda nesta introducao, entao
    o risco documentado em IAC.md nao se materializa agora). Nota
    importante: OCI nao permite converter um IP efemero em reservado no
    mesmo endereco - so criando um novo IP reservado (endereco diferente)
    e migrando o DNS. Se o IP for reservado no futuro, isso exige janela
    de manutencao planejada com atualizacao do registro DNS de
    itcenter-daniel.chickenkiller.com.

[x] Levantar todos os OCIDs existentes (VCN, subnets, IGW, route table, security list, instancia)

    Levantados via oci CLI em 2026-08-04. Descoberta importante nao
    prevista em IAC.md/NETWORK.md: a VCN foi criada pelo "VCN Wizard" da
    Oracle, que tambem provisionou um NAT Gateway e um Service Gateway
    (fora do escopo do Terraform - so referenciados por OCID). A subnet
    privada usa uma route table e uma security list dedicadas (nao a
    default da VCN, que na verdade pertence a subnet publica) com rota
    real para o NAT Gateway - ou seja, a subnet privada ja tem saida de
    internet configurada, nao esta "sem uso" como a documentacao antiga
    sugeria. Ver docs/architecture/IAC.md e NETWORK.md atualizados.

[x] Criar infra/terraform/modules/network

    Ajustado em 2026-08-04 apos a descoberta acima: adicionadas as
    variaveis private_route_table_id/private_security_list_ids (a
    subnet privada nao usa mais oci_core_vcn.this.default_route_table_id/
    default_security_list_id), adicionadas as 2 regras ICMP padrao do
    VCN Wizard na security list publica, display_names ajustados para
    bater com os nomes reais ja existentes, e criado versions.tf
    proprio do modulo (faltava - sem ele o Terraform resolvia o
    provider como hashicorp/oci em vez de oracle/oci). Importado com
    sucesso contra producao, plan limpo.

[x] Criar infra/terraform/modules/compute

    Corrigido bug de schema em 2026-08-04: source_details usava
    `image_id`, mas o provider oracle/oci >= 5.x espera `source_id`.
    Criado versions.tf proprio do modulo (mesmo motivo do network).
    Importado com sucesso contra producao com diff zero.

[x] Criar infra/terraform/environments/production

    main.tf, variables.tf e terraform.tfvars.example atualizados em
    2026-08-04 com as novas variaveis private_route_table_id/
    private_security_list_ids e correcao do exemplo de shape.
    terraform.tfvars real preenchido com os valores de producao
    (gitignored, nao versionado).

[x] Fixar versions.tf (provider oci e terraform)

    infra/terraform/environments/production/versions.tf ja existia:
    terraform >= 1.6, provider oracle/oci ~> 5.0 (resolveu para 5.47.0).
    Adicionado versions.tf tambem em modules/network e modules/compute
    em 2026-08-04 (ver acima) - sem eles os modulos nao herdavam o
    source oracle/oci corretamente.

[x] terraform init com backend local

    Executado em 2026-08-04 (backend local, terraform.tfstate
    gitignored).

[x] Importar VCN e validar plan sem diff

[x] Importar Internet Gateway e validar plan sem diff

[x] Importar Route Table e validar plan sem diff

[x] Importar Security List e validar plan sem diff

[x] Importar subnet publica e validar plan sem diff

[x] Importar subnet privada e validar plan sem diff

[x] Importar instancia de computacao e validar plan sem diff

    Diff zero de primeira (shape, imagem, subnet e chave SSH bateram
    exatamente) - so depois de corrigir o bug image_id -> source_id.

[x] Importar IP publico reservado, se aplicavel

    Nao aplicavel: IP e efemero (ver item acima), decisao foi nao
    reservar agora. Nenhum recurso oci_core_public_ip foi criado.

[x] Confirmar terraform plan completo em "No changes."

    Alcancado em 2026-08-04 apos um pequeno apply so de tags (0 add,
    6 change, 0 destroy - remocao da tag "VCN" que o VCN Wizard deixa
    em todo recurso de rede, normalizada para freeform_tags = {}).
    `terraform plan` final retornou "No changes. Your infrastructure
    matches the configuration."

[x] Adicionar lifecycle prevent_destroy na instancia e na VCN

    Ja estava no codigo dos modulos desde a criacao inicial; validado
    que sobreviveu ao import sem problema.

[ ] Criar bucket OCI Object Storage para state remoto

[ ] Migrar state para backend remoto (terraform init -migrate-state)

[ ] Implementar infra/bootstrap/{01-system,02-packages,03-directories,04-docker,05-firewall,bootstrap}.sh conforme docs/deployment/BOOTSTRAP.md

[ ] Documentar variavel opcional de cloud-init/bootstrap no module compute (sem ativar em producao)

---

# EPIC 16 - Hardening do Agente Windows

Objetivo:

Corrigir lacunas concretas de robustez identificadas no agente PowerShell (agent-windows/), mantendo a linguagem atual conforme ADR-025.

### Tarefas

[x] Restringir ACL de config.json (leitura apenas para SYSTEM/Administrators) para proteger o agent_api_key em texto puro

[x] Adicionar quarentena para arquivo de cache corrompido em Send-PendingAgentCheckins, evitando que um arquivo quebrado trave o reenvio dos mais novos

[x] Adicionar retencao/limite de idade para arquivos em cache/

[x] Adicionar rotacao por tamanho para logs/itcenter-agent.log

[x] Trocar medicao de CPU de Win32_Processor.LoadPercentage para Get-Counter '\Processor(_Total)\% Processor Time' amostrado

[x] Incluir apps UWP/Store (Get-AppxPackage) no inventario de programas instalados

[x] Ampliar deteccao de USB para alem de armazenamento (Win32_PnPEntity), mantendo a politica de nao ler conteudo

[x] Adicionar try/catch no nivel mais alto de Start-ItCenterAgent com log explicito de falha de configuracao

[x] Assinar os scripts do agente com certificado de code-signing e trocar ExecutionPolicy de Bypass para AllSigned ou RemoteSigned

    Decisao registrada em ADR-031 (2026-08-10): certificado Authenticode
    self-signed (New-SelfSignedCertificate -Type CodeSigningCert, validade
    de 10 anos, sem custo de CA publica) + ExecutionPolicy AllSigned (nao
    RemoteSigned, que nao verifica scripts sobrescritos localmente sem
    Zone.Identifier de Internet). Implementado em 2026-08-10:
    agent-windows/scripts/New-AgentSigningCertificate.ps1 e
    Sign-AgentScripts.ps1 criados; install-agent.ps1 importa
    itcenter-agent-signing.cer em Cert:\LocalMachine\Root e
    Cert:\LocalMachine\TrustedPublisher antes de validar a assinatura dos
    scripts de origem (ordem necessaria: numa maquina nova a cadeia de
    confianca so existe apos o import), copia os arquivos e registra a
    Tarefa Agendada com ExecutionPolicy AllSigned (fallback
    -SkipSignatureCheck para instalacao local/dev, volta a Bypass);
    uninstall-agent.ps1 remove o certificado com -RemoveFiles. Import/
    remocao usam certutil.exe em vez da API .NET X509Store: descoberto
    durante a validacao que X509Store.Add() na store Root pode travar
    esperando um prompt de seguranca do Windows mesmo chamado via script,
    o que quebraria uma instalacao silenciosa em massa; certutil.exe nao
    tem esse problema. Chave privada (.pfx) nunca versionada nem usada em
    CI; geracao do certificado real de producao e assinatura dos scripts
    de producao ficam a cargo do mantenedor, fora desta implementacao.
    docs/agent/INSTALLATION.md e TROUBLESHOOTING.md atualizados.

[x] Atualizar docs/agent/TROUBLESHOOTING.md com os novos comportamentos apos o hardening

---

# EPIC 17 - Hardening do Dashboard (Frontend)

Objetivo:

Corrigir os riscos concretos identificados na auditoria de seguranca do frontend (`frontend/dashboard/`) em 2026-07-29, mantendo Next.js/React como stack oficial. Nenhuma chave de banco ou de backend foi encontrada no codigo; os itens abaixo sao superficie de ataque client-side e lacunas de defesa em profundidade. Prioridade atribuida por risco, do mais critico para o mais baixo.

### Tarefas - Prioridade Alta

[x] Migrar o token de autenticacao de localStorage para cookie httpOnly + Secure + SameSite=Strict, setado no login e lido pelo proxy /api/backend a partir do cookie (revisar contrato do ADR-022 antes de implementar)

[x] Adicionar security headers no frontend (Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, Referrer-Policy) via next.config.mjs, apos confirmar quais ja sao aplicados pelo Nginx para evitar duplicidade (CSP adicionada; os outros 3 ja vem do Nginx e nao foram duplicados)

### Tarefas - Prioridade Media

[x] Remover o fallback NEXT_PUBLIC_API_BASE_URL do proxy app/api/backend/[...path]/route.ts, mantendo somente ITCENTER_API_BASE_URL

[x] Criar middleware.ts no frontend para checar sessao no edge antes de renderizar paginas protegidas

[x] Restabelecer auditoria de dependencias do frontend (npm audit) rodando em ambiente com acesso direto ao registry (ex.: GitHub Actions) e registrar na rotina semanal

### Tarefas - Prioridade Baixa

[x] Adicionar .env* ao .dockerignore do frontend como prevencao

[x] Avaliar allowlist explicita de rotas no proxy /api/backend/[...path] em vez de repassar qualquer path (implementada)

[x] Confirmar com o backend se mensagens de erro (campo detail) podem vazar detalhes internos antes de continuar exibindo-as diretamente na UI (confirmado: nenhum detail interpola exceção interna)

### Tarefas - Documentacao

[x] Atualizar docs/security/AUTH.md, docs/security/SECURITY.md e docs/architecture/SECURITY.md removendo cada risco da lista conforme for corrigido

---

# EPIC 18 - Orquestracao de Agentes de IA (Claude Code nativo)

Objetivo:

Configurar o Claude Code para atuar como especialistas de dominio (backend, frontend, devops, security, architecture, documentation) usando apenas recursos nativos (subagents, slash commands, Workflow tool), conforme ADR-026. Sem framework Python proprio, sem Strix/OpenAI/Gemini.

### Tarefas

[x] Criar subagents em .claude/agents/ (backend, frontend, devops, security, architecture, documentation)

[x] Criar slash commands em .claude/commands/ (/backend, /frontend, /devops, /security, /architecture, /docs)

[x] Criar comando /feature com pipeline via Workflow tool (architecture -> implementation -> review + security -> docs)

[x] Criar docs/development/AI_WORKFLOW.md documentando a convencao e o que foi descartado

[x] Registrar ADR-026 em docs/development/DECISIONS.md

### Tarefas - Futuro (fora de escopo agora)

[ ] Avaliar Strix isolado para teste de seguranca autorizado (pentest formal), como decisao propria com ADR proprio, se e quando surgir necessidade real

[ ] Configurar hooks em .claude/settings.json somente se aparecer um gatilho concreto (ex.: rodar pytest automaticamente apos editar backend/)

---

# EPIC 19 - Hub de Integracao: RustDesk e Snipe-IT

Objetivo:

Implementar as duas primeiras integracoes do Hub (Fase H de `docs/architecture/FUTURE_ARCHITECTURE.md`), priorizadas em 2026-08-03 por serem as de menor esforco e maior valor imediato de produto (ver ADR-027 e ADR-028). Backend e frontend implementados em 2026-08-04, com revisao de seguranca aplicada (RBAC do botao "Conectar" corrigido no cliente; sincronizacao Snipe-IT movida para `BackgroundTasks` para nao atrasar o check-in sob lentidao do Snipe-IT). Execucao real dos testes novos (`pytest`) validada em 2026-08-11 com PostgreSQL local via Docker Compose: suite completa com 87 passed, incluindo os 7 testes de `test_snipeit_service.py` e os 5 de `test_machines_rustdesk.py`. EPIC 19 encerrada.

### Tarefas - RustDesk (ADR-027)

[x] Adicionar coluna `machines.rustdesk_id` (nullable) via migration

[x] Endpoint `PATCH /api/v1/machines/{id}/rustdesk` para admin/analyst cadastrarem o ID (viewer sem acesso de escrita)

[x] Botao "Conectar" em `MachineDetailView` (abre `rustdesk://connect?id=...` via URI customizado do RustDesk)

[x] Indicar no `MachinesView`/`MachineDetailView` se a maquina tem RustDesk cadastrado

[x] Atualizar `docs/backend/DATABASE.md`, `docs/backend/API.md` e `docs/security/AUTH.md` no momento da implementacao (nao antes, para nao descrever schema/endpoint que ainda nao existe)

### Tarefas - Snipe-IT (ADR-028)

[x] Criar servico de integracao (`app/services/snipeit.py`) consumindo a API REST do Snipe-IT

[x] Adicionar `SNIPEIT_BASE_URL` e `SNIPEIT_API_TOKEN` como secrets, nunca versionados (`.env.production.example`, `docs/security/SECURITY.md`)

[x] Adicionar coluna `machines.snipeit_asset_id` (nullable) via migration

[x] Sincronizacao automatica no check-in: existe no Snipe-IT -> atualiza; nao existe -> cria (falha do Snipe-IT nao bloqueia o check-in)

[x] Link "Ver no Snipe-IT" no `MachineDetailView` (aponta para a URL do ativo, sem espelhar todos os campos do Snipe-IT no banco do IT Center)

[x] Atualizar `docs/backend/DATABASE.md`, `docs/backend/API.md` e `docs/security/SECURITY.md` no momento da implementacao

---

# EPIC 20 - Relatorios PDF e Dashboard Executivo

Objetivo:

Entregar exportacao de relatorios em PDF e uma visao executiva resumida do dashboard (ADR-029). Somente planejamento/documentacao nesta rodada.

### Tarefas

[ ] Escolher e adicionar ao backend a biblioteca de geracao de PDF (ver alternativas avaliadas na ADR-029)

[ ] Endpoint agregado `GET /api/v1/dashboard/summary` (maquinas online/offline, alertas por severidade, eventos recentes) para alimentar a tela executiva sem N chamadas do frontend

[ ] Tela "Dashboard Executivo" no frontend (nova rota; leitura liberada para `admin`/`analyst`/`viewer`, mesmo padrao de RBAC das telas atuais)

[ ] Endpoint(s) de exportacao PDF (ex.: `GET /api/v1/machines/{id}/report.pdf`, `GET /api/v1/reports/executive.pdf`)

[ ] Botao de exportar PDF na tela executiva e/ou no detalhe da maquina

[ ] Atualizar `docs/backend/API.md` e `frontend/dashboard/README.md` no momento da implementacao

---

# EPIC 21 - Observabilidade de Infraestrutura (Prometheus + Grafana)

Objetivo:

Monitorar o Edge Node e os containers — nao as maquinas Windows monitoradas pelo agente, que ja tem metricas proprias (`metrics`, EPIC 3) e plano de retencao proprio (Fase E de `docs/architecture/FUTURE_ARCHITECTURE.md`). Escopo corrigido em 2026-08-03: a ideia original de "Prometheus + Grafana" na EPIC 14 arriscava duplicar o pipeline de metricas do agente; aqui o alvo e a infraestrutura (ADR-030, Fase F de `docs/architecture/FUTURE_ARCHITECTURE.md`). Somente planejamento/documentacao nesta rodada.

### Tarefas

[ ] Adicionar `node_exporter` (metricas de host: CPU/RAM/disco/rede da VM) ao `infra/docker-compose.production.yml`

[ ] Adicionar cAdvisor ou metricas nativas do Docker para saude dos containers

[ ] Adicionar Prometheus com scrape config apontando para `node_exporter`/cAdvisor

[ ] Adicionar Grafana com dashboard(s) pre-configurado(s) para saude do Edge Node

[ ] Garantir que Prometheus/Grafana NAO sejam expostos publicamente (Nginx continua unico ponto de entrada; acesso via tunel SSH ou rota autenticada)

[ ] Validar impacto de recursos (RAM/disco) no free tier antes de ativar em producao (ver `infra/scripts/ops-check.sh`)

[ ] Atualizar `docs/architecture/ARCHITECTURE.md`, `docs/architecture/CONTAINERS.md`, `docs/architecture/NETWORK.md` e `docs/security/SECURITY.md` no momento da implementacao

---

# EPIC 22 - Auto-atualizacao do Agente Windows (Updater Dedicado)

Objetivo:

Implementar atualizacao automatica do agente Windows via um updater dedicado, 100% PowerShell puro, com Tarefa Agendada propria e frequencia menor que o check-in de coleta (ADR-032). Sem Servico Windows nativo via SCM, sem NSSM/WinSW. Resolve, apenas para este caso, o item "Criar servico Windows" da Fase B de `docs/architecture/FUTURE_ARCHITECTURE.md`; o caso geral (servico Windows para a coleta em si) continua pendente. Somente planejamento/documentacao nesta rodada.

### Tarefas

[ ] Endpoint `GET /api/v1/agent/manifest` retornando `{version, sha256}` da versao publicada do agente

[ ] Endpoint `GET /api/v1/agent/download` (ou similar) para baixar o script mais recente, assinado com o certificado do ADR-031

[ ] Adicionar coluna `machines.agent_version` (nullable) via migration

[ ] Adicionar coluna `machines.target_agent_version` (nullable) via migration

[ ] Persistir `agent_version` a cada check-in (agente passa a informar a propria versao no payload)

[ ] Adicionar `$script:AgentVersion` no topo de `itcenter-agent.ps1`

[ ] Criar `agent-windows/itcenter-agent-updater.ps1` (download do manifest/script, backup do script atual, substituicao atomica via `Move-Item -Force`)

[ ] Validacao obrigatoria de assinatura Authenticode (`Get-AuthenticodeSignature` Status `Valid`) e hash SHA-256 no updater, sem fallback `-SkipSignatureCheck`

[ ] Auto-rollback: restaurar `itcenter-agent.ps1.previous` apos N check-ins consecutivos com falha pos-atualizacao, com log da falha

[ ] Registrar Tarefa Agendada dedicada `ITCenterAgentUpdater` em `install-agent.ps1` (frequencia configuravel, menor que o check-in de coleta)

[ ] Exibir `agent_version` no dashboard (telas de maquina)

[ ] Atualizar `docs/backend/API.md`, `docs/backend/DATABASE.md`, `docs/agent/CHECKIN.md` e `docs/agent/INSTALLATION.md` no momento da implementacao
