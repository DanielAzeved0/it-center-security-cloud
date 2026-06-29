# Oracle Cloud Deployment

Este documento descreve a implantacao do IT Center Security Cloud em uma VM da Oracle Cloud usando Ubuntu 24.04 LTS, Docker, Docker Compose, Nginx e Let's Encrypt.

## Ambiente implantado

```text
Cloud provider: Oracle Cloud
Sistema: Ubuntu Server 24.04 LTS
Dominio: itcenter-daniel.chickenkiller.com
IP publico: 147.15.78.220
Runtime: Docker Engine + Docker Compose
Rede Docker: itcenter-network
Diretorio da aplicacao: /opt/itcenter/app/it-center-security-cloud
Backups: /opt/itcenter/backups
```

## Arquitetura de producao

```mermaid
flowchart TD
    internet[Internet] --> dns[DNS<br/>itcenter-daniel.chickenkiller.com]
    dns --> vm[Oracle Cloud VM<br/>Ubuntu 24.04 LTS]
    vm --> docker[Docker Engine]
    docker --> nginx[Nginx Reverse Proxy<br/>80/443]
    docker --> frontend[Next.js Dashboard<br/>3000 interno]
    docker --> backend[FastAPI Backend<br/>8000 interno]
    docker --> postgres[PostgreSQL<br/>5432 interno]
    nginx --> frontend
    nginx --> backend
    backend --> postgres
```

## Etapas realizadas

1. Instalar Docker Engine.
2. Instalar Docker Compose.
3. Adicionar o usuario `ubuntu` ao grupo `docker`.
4. Validar instalacao:

```bash
docker --version
docker compose version
```

5. Configurar chave SSH da Oracle VM no GitHub.
6. Clonar o repositorio privado:

```bash
git clone git@github.com:DanielAzeved0/it-center-security-cloud.git
```

7. Criar `.env.production` a partir de `.env.production.example`.
8. Gerar secrets com:

```bash
openssl rand -hex 32
```

9. Criar `.secrets/dashboard.htpasswd` para HTTP Basic Auth.
10. Validar `infra/docker-compose.production.yml`.
11. Executar preflight de producao.
12. Emitir certificado Let's Encrypt.
13. Executar deploy.
14. Validar containers e healthchecks.

## Checklist Oracle Cloud

- [ ] VM Ubuntu 24.04 LTS criada.
- [ ] IP publico associado.
- [ ] Porta 22 liberada apenas para origem administrativa.
- [ ] Porta 80 liberada para emissao/renovacao TLS.
- [ ] Porta 443 liberada para HTTPS.
- [ ] Portas 3000, 8000 e 5432 nao expostas publicamente.
- [ ] DNS apontando para o IP publico.
- [ ] Docker instalado.
- [ ] Docker Compose instalado.
- [ ] Repositorio clonado em `/opt/itcenter/app`.
- [ ] `.env.production` criado fora do Git.
- [ ] `.secrets/dashboard.htpasswd` criado fora do Git.
- [ ] Certificado TLS emitido.
- [ ] Containers healthy.

## Estado atual

A infraestrutura esta funcional:

```text
HTTPS: ativo
Nginx: funcionando
Dashboard: funcionando
Backend: funcionando
PostgreSQL: funcionando
Containers: healthy
Windows Agent: integrado ao check-in de producao quando DNS e API key estao corretos
```

O dashboard pode aparecer vazio ate que o Windows Agent envie o primeiro check-in. Esse comportamento e esperado.
