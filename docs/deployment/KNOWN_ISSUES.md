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

## PostgreSQL no mesmo Edge Node

No MVP, PostgreSQL roda no mesmo host por custo zero.

Risco:

* Nao ha alta disponibilidade.

Evolucao futura:

* Instancia privada dedicada.
* Banco gerenciado.
* Backups automatizados externos.
