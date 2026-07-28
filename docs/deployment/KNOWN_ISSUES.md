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

## PostgreSQL no mesmo Edge Node

No MVP, PostgreSQL roda no mesmo host por custo zero.

Risco:

* Nao ha alta disponibilidade.

Evolucao futura:

* Instancia privada dedicada.
* Banco gerenciado.
* Backups automatizados externos.
