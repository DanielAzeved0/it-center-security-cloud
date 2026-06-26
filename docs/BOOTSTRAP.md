# Bootstrap versionado do Edge Node

Este documento registra a decisao de introduzir um bootstrap reproduzivel para o Edge Node do IT Center Security Cloud.

O objetivo e evitar que a preparacao da VM dependa de comandos manuais soltos. A configuracao inicial deve virar parte oficial do repositorio, com scripts versionados, revisaveis e reutilizaveis em qualquer nova VM.

## Contexto

Antes de instalar e configurar a aplicacao, o projeto precisa preparar o host Linux de forma consistente.

O ambiente alvo continua sendo:

```text
Oracle Cloud Free Tier
Ubuntu Server 24.04 LTS
Edge Node: itcenter-edge-01
Raiz operacional: /opt/itcenter
```

## Decisao

Antes de instalar a aplicacao, o projeto deve documentar e depois implementar um bootstrap versionado em:

```text
infra/
`-- bootstrap/
    |-- 01-system.sh
    |-- 02-packages.sh
    |-- 03-directories.sh
    |-- 04-docker.sh
    |-- 05-firewall.sh
    `-- bootstrap.sh
```

Esse bootstrap sera responsavel por preparar a VM. Ele nao deve publicar a aplicacao imediatamente.

## Sequencia planejada

### 01-system.sh

Responsavel por:

* validar Ubuntu Server;
* configurar hostname `itcenter-edge-01`;
* atualizar os pacotes do sistema;
* configurar timezone;
* falhar cedo se o ambiente nao for suportado.

### 02-packages.sh

Responsavel por instalar ferramentas basicas:

* `curl`;
* `git`;
* `ca-certificates`;
* `gnupg`;
* `ufw`;
* `openssl`;
* utilitarios operacionais necessarios ao bootstrap.

### 03-directories.sh

Responsavel por criar a estrutura oficial:

```text
/opt/itcenter/
|-- app/       # destino futuro do clone do repositorio
|-- backups/   # dumps e artefatos de backup
|-- configs/   # configuracoes operacionais externas ao Git
|-- logs/      # logs operacionais do host
|-- scripts/   # automacoes do host
`-- secrets/   # segredos externos ao Git, quando necessario
```

Essa etapa prepara o host, mas nao clona o repositorio e nao cria secrets reais.

### 04-docker.sh

Responsavel por instalar:

* Docker CE;
* Docker CLI;
* Docker Compose Plugin;
* Buildx;
* habilitacao do servico Docker no boot.

### 05-firewall.sh

Responsavel por configurar UFW:

* negar entrada por padrao;
* permitir saida por padrao;
* permitir SSH, idealmente restrito ao IP administrativo;
* permitir HTTP `80`;
* permitir HTTPS `443`;
* manter portas internas `3000`, `8000` e `5432` sem exposicao publica.

### bootstrap.sh

Responsavel por orquestrar os scripts na ordem oficial:

```text
01-system.sh
02-packages.sh
03-directories.sh
04-docker.sh
05-firewall.sh
```

## Fora do escopo do bootstrap

O bootstrap nao deve:

* clonar automaticamente a aplicacao;
* preencher `.env.production`;
* gerar ou armazenar secrets;
* emitir certificado TLS;
* subir Docker Compose;
* executar migrations;
* publicar Nginx, FastAPI, Next.js ou PostgreSQL.

Essas atividades pertencem ao fluxo de deploy documentado em `docs/DEPLOYMENT.md`.

## Beneficios esperados

* Recriar uma VM com menos risco de erro manual.
* Subir uma segunda VM seguindo o mesmo padrao.
* Tornar a infraestrutura mais profissional e auditavel.
* Facilitar revisao de mudancas de infraestrutura via Git.
* Separar claramente preparacao do host e deploy da aplicacao.

## Criterios para implementacao futura

Quando os scripts forem criados, eles devem:

* ser idempotentes sempre que possivel;
* usar `set -eu`;
* validar execucao como root quando necessario;
* nao conter secrets;
* nao apagar diretorios com dados sem confirmacao explicita;
* registrar mensagens claras de progresso;
* falhar cedo quando uma premissa nao for atendida;
* ser documentados antes de uso em producao.

## Fluxo futuro esperado

Em uma nova VM, o fluxo desejado sera:

```bash
git clone <repo-url> /opt/itcenter/app
cd /opt/itcenter/app
sudo sh infra/bootstrap/bootstrap.sh
```

Depois disso, o operador segue o deploy de producao:

```text
1. configurar .env.production;
2. criar .secrets/dashboard.htpasswd;
3. apontar DNS;
4. emitir certificado TLS;
5. executar preflight;
6. subir docker-compose.production.yml.
```
