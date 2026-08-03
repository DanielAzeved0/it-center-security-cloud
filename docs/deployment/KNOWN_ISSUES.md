# Known Issues

## Confirmacao EPIC 9

Data:

```text
2026-07-03
```

Status:

```text
Pendencia documental confirmada.
```

As falhas e limitacoes conhecidas do fluxo fim a fim estao registradas neste documento. Nao ha novo bloqueio funcional reportado para impedir o encerramento da EPIC 9; os itens abaixo permanecem como riscos operacionais conhecidos ou limitacoes do MVP.

## DNS da Vivo com propagacao lenta

Foi observado que o dominio `itcenter-daniel.chickenkiller.com` resolvia corretamente em Google DNS, Cloudflare e Quad9, mas ainda nao propagava no DNS da Vivo.

Classificacao:

```text
Problema externo ao projeto
```

Acao:

* Aguardar propagacao.
* Testar resolvers publicos.
* Evitar alterar infraestrutura quando outros resolvers ja resolvem corretamente.
* Corrigir DNS no roteador/DHCP para evitar editar `hosts` em cada maquina.
* Avaliar dominio proprio em Cloudflare para o endpoint dos agentes.

## VM com pouca memoria

Oracle Free Tier pode ter pouca memoria disponivel para build e containers.

Mitigacao aplicada:

* Criacao de Swap.

Risco:

* Builds podem ficar lentos.
* Uso intenso de swap degrada performance.

## Basic Auth e controle administrativo

HTTP Basic Auth protege o dashboard no MVP.

Limitacao:

* Nao substitui login completo com usuarios, sessoes, RBAC e auditoria.

Evolucao esperada:

* Implementar governanca de usuarios em fase futura.

## Rollback e migrations

Rollback de aplicacao nao desfaz migrations automaticamente.

Regra:

* Migrations devem ser retrocompativeis.
* Fazer backup antes de atualizar.

## Criacao do primeiro admin nao e automatica

`backend/create_admin.py` nao faz parte da imagem Docker do backend e nao roda como parte do `deploy.sh`.

Risco:

* Um ambiente novo (ou um restore que recrie o volume do banco do zero) pode ficar sem nenhum usuario administrativo ate que o script seja executado manualmente. Ja aconteceu em producao (INCIDENTE 019 em `POSTMORTEMS.md`).

Mitigacao atual:

* Executar `create_admin.py` manualmente apos qualquer provisionamento novo do banco (`docker cp` para dentro do container e `docker exec`).

Evolucao esperada:

* Incluir o script na imagem ou chama-lo de forma idempotente a partir de `deploy.sh`.

## Basic Auth nao pode competir com o cabecalho Authorization da aplicacao

O Nginx aplica Basic Auth via cabecalho `Authorization: Basic ...`. Qualquer rota que o dashboard chame usando `Authorization: Bearer <token>` perde a credencial Basic Auth do ponto de vista do Nginx, pois o HTTP so permite um `Authorization` por requisicao.

Mitigacao atual:

* Rotas de API chamadas pela SPA com Bearer token (`/api/backend/`) sao isentas de `auth_basic` no Nginx (ADR-023), protegidas apenas pelo RBAC/token da aplicacao.

Risco:

* Qualquer nova rota publica adicionada sob `location /` que tambem exija Bearer token reproduzira o mesmo loop de login (INCIDENTE 020 em `POSTMORTEMS.md`) se nao for isenta de Basic Auth da mesma forma.

## Auditoria de dependencias do frontend bloqueada no ambiente de desenvolvimento

Durante a auditoria de seguranca do frontend em 2026-07-29, `npm audit` em `frontend/dashboard/` falhou com `self-signed certificate in certificate chain` ao tentar acessar `registry.npmjs.org` a partir do ambiente de desenvolvimento atual (proxy corporativo intercepta TLS).

Risco:

* Nao ha confirmacao automatizada de CVEs em `next@16.2.12`/`react@19.2.3` e demais dependencias diretas do dashboard a partir do ambiente de desenvolvimento local, alem do que o Docker Scout ja cobre na imagem final (ver `docs/security/SECURITY.md`).

Mitigacao atual:

* `docker scout cves infra-frontend:latest --only-severity critical,high` continua sendo a validacao oficial antes de publicar a imagem (ja documentado em `docs/security/SECURITY.md`).
* O passo `Audit frontend dependencies` do workflow `ci.yml` (GitHub Actions, sem o proxy corporativo local) roda `npm audit --audit-level=high` a cada push/PR e ja provou seu valor em 2026-08-03: pegou 3 CVEs high reais em `next@16.2.9` (bypass de middleware/proxy, SSRF em rewrites, DoS em Server Actions) e mais duas em dependencias internas do Next (`postcss`, `sharp`). Corrigido com bump para `next@16.2.12` e `overrides` de `postcss`/`sharp` em `package.json` (ver `docs/security/SECURITY.md`).

Evolucao esperada:

* Se for necessario rodar `npm audit`/`npm install` localmente antes de abrir PR, o bloqueio de TLS pode ser contornado pontualmente exportando a cadeia de certificado do proxy/antivirus (`openssl s_client -connect registry.npmjs.org:443 -showcerts`) e apontando `NODE_EXTRA_CA_CERTS` para esse arquivo — nao adicionar isso como configuracao permanente do repositorio nem desabilitar `strict-ssl`.

## .dockerignore do frontend nao exclui arquivos .env*

`frontend/dashboard/.dockerignore` hoje so ignora `node_modules`, `.next` e `*.log`. Nao existe nenhum `.env` no repositorio, entao nao ha vazamento ativo, mas o `Dockerfile` faz `COPY . .` no estagio de build sem essa exclusao.

Risco:

* Se um `.env.local` for criado no futuro para desenvolvimento e esquecido, valores de `NEXT_PUBLIC_*` seriam embutidos estaticamente no build da imagem Docker.

Evolucao esperada:

* Adicionar `.env*` ao `.dockerignore` do frontend como prevencao. Rastreado na EPIC 17 de `docs/development/TASKS.md`.

## PostgreSQL no mesmo Edge Node

No MVP, PostgreSQL roda no mesmo host por custo zero.

Risco:

* Nao ha alta disponibilidade.

Evolucao futura:

* Instancia privada dedicada.
* Banco gerenciado.
* Backups automatizados externos.
