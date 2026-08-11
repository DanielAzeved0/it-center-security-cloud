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

[x] Coletar MAC Address (adicionado em 2026-08-11)

    Get-AgentNetworkInfo substitui Get-AgentIpAddress e retorna IP e MAC
    da mesma interface de rede selecionada (mesma logica de fallback em
    cascata: Get-NetIPAddress+Get-NetAdapter -> Win32_NetworkAdapterConfiguration
    -> resolucao DNS, sem MAC nesse ultimo nivel). Normalizado para o
    formato AA:BB:CC:DD:EE:FF. Persistido em machines.mac_address
    (migration 007_machines_mac_address.sql), exposto em GET /machines
    e GET /machines/{id}, exibido no detalhe da maquina no dashboard.
    docs/agent/CHECKIN.md, docs/backend/API.md e docs/backend/DATABASE.md
    atualizados.

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

[ ] Hub de integracao com ferramentas open source maduras, em vez de substitui-las (arquitetura detalhada em docs/architecture/FUTURE_ARCHITECTURE.md, Fase H). RustDesk saiu daqui e ganhou plano concreto na EPIC 19; NetBox continua aspiracional.

[ ] Integracao Snipe-IT (ITAM: patrimonio, garantia, licencas). Implementada e revertida em 2026-08-11 (ADR-028 -> ADR-033): nunca existiu um Snipe-IT real conectado em producao (SNIPEIT_BASE_URL nunca configurado), sem necessidade concreta de ITAM identificada. Revisitar apenas se surgir essa necessidade real - nesse caso, decidir tambem onde hospedar o Snipe-IT (self-hosted na mesma VM arrisca OOM na itcenter-edge-01 de 1GB; uma segunda VM Always Free e a opcao mais provavel).

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

EPIC 18 encerrada em 2026-08-11: todas as tarefas do escopo real (subagents,
slash commands, /feature, AI_WORKFLOW.md, ADR-026) estao concluidas. Os 2
itens acima permanecem deliberadamente nao marcados - sao gatilhos
condicionais (pentest formal com ADR proprio; automacao com gatilho
concreto), nao pendencias do MVP, conforme ja documentado em
docs/development/AI_WORKFLOW.md ("O que foi deliberadamente descartado").
Revisitar apenas se e quando a condicao de cada um se materializar.

---

# EPIC 19 - Hub de Integracao: RustDesk

Objetivo:

Implementar a primeira integracao do Hub (Fase H de `docs/architecture/FUTURE_ARCHITECTURE.md`), priorizada em 2026-08-03 por ser a de menor esforco e maior valor imediato de produto (ver ADR-027). Backend e frontend implementados em 2026-08-04, com revisao de seguranca aplicada (RBAC do botao "Conectar" corrigido no cliente). Execucao real dos testes novos (`pytest`) validada em 2026-08-11 com PostgreSQL local via Docker Compose. EPIC 19 encerrada.

A integracao com Snipe-IT (ADR-028) tambem foi implementada nesta EPIC, mas foi **revertida em 2026-08-11** (ver ADR-033): nunca existiu um Snipe-IT real conectado em producao, sem necessidade concreta de ITAM identificada. Codigo, testes, coluna `machines.snipeit_asset_id` e a secao correspondente no dashboard foram removidos; a ideia migrou para EPIC 14 (Melhorias Futuras) como item aspiracional. RustDesk nao foi afetado.

### Tarefas - RustDesk (ADR-027)

[x] Adicionar coluna `machines.rustdesk_id` (nullable) via migration

[x] Endpoint `PATCH /api/v1/machines/{id}/rustdesk` para admin/analyst cadastrarem o ID (viewer sem acesso de escrita)

[x] Botao "Conectar" em `MachineDetailView` (abre `rustdesk://connect?id=...` via URI customizado do RustDesk)

[x] Indicar no `MachinesView`/`MachineDetailView` se a maquina tem RustDesk cadastrado

[x] Atualizar `docs/backend/DATABASE.md`, `docs/backend/API.md` e `docs/security/AUTH.md` no momento da implementacao (nao antes, para nao descrever schema/endpoint que ainda nao existe)

### Tarefas - Snipe-IT (ADR-028) — revertidas em 2026-08-11, ver ADR-033

[x] ~~Criar servico de integracao (`app/services/snipeit.py`) consumindo a API REST do Snipe-IT~~ (implementado em 2026-08-04, removido em 2026-08-11)

[x] ~~Adicionar `SNIPEIT_BASE_URL` e `SNIPEIT_API_TOKEN` como secrets~~ (removidos de `.env.production.example`/`docs/security/SECURITY.md` em 2026-08-11)

[x] ~~Adicionar coluna `machines.snipeit_asset_id` (nullable) via migration~~ (removida pela migration `006_remove_machines_snipeit.sql`)

[x] ~~Sincronizacao automatica no check-in~~ (removida, ver `app/services/agent.py`)

[x] ~~Link "Ver no Snipe-IT" no `MachineDetailView`~~ (removido do dashboard)

[x] Atualizar `docs/backend/DATABASE.md`, `docs/backend/API.md` e `docs/security/SECURITY.md` refletindo a remocao

---

# EPIC 20 - Relatorios PDF e Dashboard Executivo

Objetivo:

Entregar exportacao de relatorios em PDF e uma visao executiva resumida do dashboard (ADR-029).

### Tarefas

[x] Escolher e adicionar ao backend a biblioteca de geracao de PDF (ver alternativas avaliadas na ADR-029)

    reportlab==5.0.0 adicionado a backend/requirements.txt. Validado em
    2026-08-11 com build real da imagem Docker Alpine do backend
    (docker build) e geracao de PDF dentro do container: instala sem
    dependencias de sistema extras, confirmando a premissa da ADR-029
    de manter a base Alpine intacta (ao contrario do WeasyPrint).

[x] Endpoint agregado `GET /api/v1/dashboard/summary` (maquinas online/offline, alertas por severidade, eventos recentes) para alimentar a tela executiva sem N chamadas do frontend

    Implementado em app/routes/dashboard.py + app/services/dashboard.py +
    app/repositories/dashboard.py, RBAC admin/analyst/viewer. Alertas
    contados como abertos quando status IN ('open', 'investigating').

[x] Tela "Dashboard Executivo" no frontend (nova rota; leitura liberada para `admin`/`analyst`/`viewer`, mesmo padrao de RBAC das telas atuais)

    components/ExecutiveDashboardView.tsx + app/executive/page.tsx, item
    de navegacao "Executivo" adicionado em Shell.tsx.

[x] Endpoint(s) de exportacao PDF (ex.: `GET /api/v1/machines/{id}/report.pdf`, `GET /api/v1/reports/executive.pdf`)

    app/routes/reports.py + app/services/reports.py (reportlab, sem
    markup HTML nas celulas de tabela para evitar que texto de
    hostname/descricao quebre o parser de Paragraph). RBAC
    admin/analyst/viewer, mesmo padrao de leitura das telas atuais.

[x] Botao de exportar PDF na tela executiva e/ou no detalhe da maquina

    Botao "Exportar PDF" em ExecutiveDashboardView.tsx e
    MachineDetailView.tsx, via novo helper downloadBackendFile em
    lib/api.ts (fetch direto ao proxy + blob, sem passar por
    requestBackend que assume JSON).

    Durante a implementacao foi corrigido um bug real no proxy
    app/api/backend/[...path]/route.ts: a funcao relay() lia toda
    resposta com response.text(), o que corrompe bytes binarios (PDF).
    Trocado para response.arrayBuffer() e Content-Disposition passou a
    ser repassado. Validado em 2026-08-11 comparando byte a byte o PDF
    obtido direto do backend com o obtido via proxy (identicos, exceto
    timestamp de geracao). ALLOWED_PATH_PREFIXES ampliado com
    api/v1/dashboard e api/v1/reports.

[x] Atualizar `docs/backend/API.md` e `frontend/dashboard/README.md` no momento da implementacao

Validacao em 2026-08-11: suite completa do backend (96 passed, incluindo
os novos testes de test_dashboard_summary.py e test_reports_pdf.py) e
build de producao do frontend (`npm run build`, TypeScript OK) com
Postgres local via Docker Compose. `next lint` esta quebrado neste
projeto independente desta EPIC - Next.js 16 removeu o comando `next
lint` embutido e o projeto nunca teve eslint/eslint-config-next
instalado; fora de escopo aqui, registrado como divida tecnica.
EPIC 20 encerrada.

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

---

# EPIC 23 - Auto-deteccao do ID do RustDesk no Agente

Objetivo:

Eliminar a digitacao manual do ID do RustDesk por maquina (ADR-027, EPIC 19) sempre que possivel: o agente Windows tenta coletar automaticamente o ID ja configurado no RustDesk instalado e envia-lo no check-in, exatamente como ja faz hoje para IP e MAC Address. O cadastro manual via `PATCH /api/v1/machines/{id}/rustdesk` continua existindo e tem prioridade de sobrescrita pelo operador - a deteccao automatica e um atalho, nunca uma obrigacao. Somente planejamento/documentacao nesta rodada (ADR-034).

Requisito explicito desta EPIC (nao negociavel na implementacao): **testar de fato os dois metodos de leitura abaixo** contra a versao real do RustDesk usada no ambiente, e **garantir que uma leitura automatica que falhe, ou uma versao/instalacao de RustDesk diferente da testada, nunca bloqueia o check-in nem impede o cadastro manual** - mesma politica de resiliencia ja aplicada em toda integracao externa deste projeto (Snipe-IT antes de ser revertido, ADR-028/033).

### Tarefas

[ ] Testar leitura do arquivo de config local do RustDesk (`RustDesk2.toml`, campo `id`) nos caminhos conhecidos por modo de instalacao (servico do sistema vs. execucao por usuario) - validar contra a versao real instalada no ambiente de testes, nao assumir o caminho/formato por documentacao de terceiros

[ ] Testar `RustDesk.exe --get-id` (captura de stdout) como metodo alternativo - validar se a flag existe e funciona na versao instalada, e se exige o servico do RustDesk em execucao

[ ] Com base no resultado real dos dois testes acima, decidir a ordem de tentativa (qual metodo e mais confiavel) e registrar em ADR-034 - esta decisao so pode ser tomada apos testar, nao antes

[ ] Só tentar a leitura automatica quando o agente ja detectar RustDesk instalado (reaproveitar `AUTHORIZED_REMOTE_TOOLS`/deteccao existente em `app/services/agent.py`, sem nova varredura de disco desnecessaria)

[ ] Tratamento explicito de falha: RustDesk instalado mas ID nao encontrado (versao diferente da testada, caminho de instalacao nao previsto, servico nao iniciado, TOML com schema diferente) - logar e seguir sem `rustdesk_id`, nunca lancar excecao que interrompa o check-in

[ ] Quando a leitura automatica funcionar, enviar `rustdesk_id` no payload de check-in (reaproveitar o campo/schema/coluna ja existentes do ADR-027, sem migration nova)

[ ] Persistencia: check-in automatico so sobrescreve `rustdesk_id` quando o valor atual estiver vazio OU quando decidirmos explicitamente que a leitura automatica deve ter precedencia sobre o valor manual (avaliar na implementacao; por padrao, nao pisar num valor cadastrado manualmente sem essa decisao)

[ ] Frontend: quando o `rustdesk_id` vier do agente, indicar a origem no dashboard (ex.: "coletado automaticamente da maquina" vs. "cadastrado manualmente"); o formulario de edicao manual continua existindo e disponivel para admin/analyst sobrescrever a qualquer momento

[ ] Atualizar `docs/agent/CHECKIN.md`, `docs/backend/API.md`, `docs/backend/DATABASE.md` e `docs/security/AUTH.md` refletindo a nova origem do campo e o comportamento de fallback

[ ] Testar explicitamente o cenario de falha antes de considerar a EPIC concluida: forcar uma versao/instalacao de RustDesk fora do caminho esperado e confirmar que o agente nao trava, nao gera erro no check-in, e o cadastro manual continua funcionando normalmente

---

# EPIC 24 - Polimento Visual do Dashboard (GSAP)

Objetivo:

Adicionar animacoes de polimento (entrada de cards/paineis/linhas, contadores animados, preenchimento das barras de metrica) nas telas ja existentes do dashboard, sem mudar nenhuma logica de dados/API — so camada visual. Avaliadas duas opcoes (GSAP e Three.js, ver ADR-035); GSAP escolhida por ser leve e ter encaixe direto com um app funcional que so precisa de polimento, nao de grafismo 3D. Implementada e encerrada em 2026-08-11.

### Tarefas

[x] Instalar a skill oficial de IA `greensock/gsap-skills` (5 das 8 skills: `gsap-core`, `gsap-react`, `gsap-timeline`, `gsap-performance`, `gsap-utils`) via `npx skills add`, para garantir uso correto da API antes de escrever qualquer animacao

    Conteudo versionado em `.agents/skills/gsap-*/SKILL.md` +
    `skills-lock.json`; symlinks de `.claude/skills/` (absolutos, por
    maquina) adicionados ao `.gitignore`, regeneraveis via
    `npx skills experimental_install`. Documentado em
    `docs/development/AI_WORKFLOW.md`.

[x] Instalar `gsap` e `@gsap/react` no frontend

[x] Criar `frontend/dashboard/lib/motion.ts` com 3 primitivas reaproveitadas em todas as telas: `useStaggerEntrance` (entrada com fade+translateY e stagger via `useGSAP`+`gsap.matchMedia`), `animateCountUp` (contador animado) e `animateProgressValue` (preenchimento de `<progress>`)

[x] Toda animacao usa apenas `transform`/`opacity` (`autoAlpha`, `y`, `scale`) — nunca `width`/`height`/`top`/`left` — e respeita `prefers-reduced-motion` via `gsap.matchMedia()`, conforme a skill oficial de performance/acessibilidade

[x] `Shell.tsx`: entrada suave do conteudo principal a cada tela/navegacao

[x] `Ui.tsx`: `StatCard` com contador animado quando `value` for numero; `LoadingBlock` com pulso sutil (desativado automaticamente com reduced-motion)

[x] Aplicar `useStaggerEntrance` em `DashboardView`, `ExecutiveDashboardView`, `MachinesView`, `AlertsView`, `SecurityView` e `MachineDetailView` (stat cards, paineis e linhas de tabela/lista)

[x] Animar o preenchimento das barras de metrica (CPU/RAM/disco) em `MetricTile` (`MachineDetailView`) e `MetricBar` (`MachinesView`) de 0 até o valor real ao carregar os dados

[x] `LoginView`: entrada (fade + escala leve) do painel de login

[x] Atualizar `frontend/dashboard/README.md` (secao "Animacoes (GSAP)")

Validacao em 2026-08-11: `npm run build` limpo (TypeScript OK). Dev
server + backend + Postgres local com dados reais (check-in real via
curl): as 6 rotas autenticadas (`/`, `/executive`, `/machines`,
`/alerts`, `/security`, `/machines/{id}`) retornaram 200 sem erro no
log do servidor. **Nao verificado visualmente em navegador real** —
sem ferramenta de automacao de browser conectada nesta sessao;
recomendado `npm run dev` + revisao visual manual antes de considerar
isso validado de ponta a ponta em produção. EPIC 24 encerrada.
