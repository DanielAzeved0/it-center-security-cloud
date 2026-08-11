# HTTPS Setup

Este documento descreve a configuracao HTTPS feita para o dominio `itcenter-daniel.chickenkiller.com`.

## Dominio

```text
Dominio: itcenter-daniel.chickenkiller.com
IP publico: 147.15.78.220
```

O dominio foi criado em provedor gratuito e apontado para o IP publico da Oracle VM.

## DNS

Validar resolucao:

```bash
dig itcenter-daniel.chickenkiller.com
nslookup itcenter-daniel.chickenkiller.com
```

Validadores externos usados:

```text
Google DNS: 8.8.8.8
Cloudflare: 1.1.1.1
Quad9: 9.9.9.9
```

Foi observado que o DNS da Vivo demorou mais para propagar. Isso foi classificado como problema de resolucao do provedor, nao da aplicacao.

## Portas necessarias

Para emissao inicial e renovacao:

```text
80/tcp  - HTTP challenge Let's Encrypt
443/tcp - HTTPS publico
```

Nao expor:

```text
3000/tcp - Next.js
8000/tcp - FastAPI
5432/tcp - PostgreSQL
```

## Certificado Let's Encrypt

Arquivos esperados:

```text
/etc/letsencrypt/live/itcenter-daniel.chickenkiller.com/fullchain.pem
/etc/letsencrypt/live/itcenter-daniel.chickenkiller.com/privkey.pem
```

Validar:

```bash
sudo ls -l /etc/letsencrypt/live/itcenter-daniel.chickenkiller.com/
```

## Nginx

Responsabilidades:

* Redirecionar HTTP para HTTPS.
* Terminar TLS.
* Aplicar HSTS.
* Proteger dashboard com HTTP Basic Auth.
* Manter endpoint do agente sem Basic Auth.
* Aplicar headers de seguranca.
* Fazer reverse proxy para frontend/backend.

## Validacao HTTPS

```bash
curl -I https://itcenter-daniel.chickenkiller.com
curl --user admin:SENHA_FORTE_AQUI https://itcenter-daniel.chickenkiller.com
```

Resultado esperado:

```text
HTTP/2 200 ou 3xx esperado
TLS valido
Basic Auth solicitado no dashboard
```

## Renovacao

A renovacao deve manter `/etc/letsencrypt` persistente no host.

Imagem usada pelo servico `certbot` (profile `maintenance`):

```text
certbot/certbot:v5.7.0
```

Lição aprendida (INCIDENTE 021 em `docs/deployment/POSTMORTEMS.md`): o Compose de produção já referenciou uma tag inexistente (`certbot/certbot:v4.21.0`), descoberta apenas quando a renovação real foi tentada, porque o serviço `certbot` só roda sob o profile `maintenance` e não aparece em smoke test nem deploy de rotina. Antes de fixar uma tag de imagem usada esporadicamente, confirme que ela existe (API do Docker Hub ou GitHub Releases do projeto).

Fluxo validado em produção (`infra/scripts/renew-tls.sh`, executado com sucesso em 2026-07-28 conforme `docs/deployment/DEPLOYMENT_HISTORY.md`):

```bash
TLS_RENEW_DRY_RUN=1 sh infra/scripts/renew-tls.sh
sh infra/scripts/renew-tls.sh
```

O script chama `docker compose ... --profile maintenance run --rm certbot renew --webroot -w /var/www/certbot` (adicionando `--dry-run` quando `TLS_RENEW_DRY_RUN=1`) e recarrega o Nginx (`nginx -s reload`) automaticamente ao final.
