# Known Issues

## Windows Agent ainda nao integrado

Estado:

```text
Pendente
```

Impacto:

* Dashboard pode aparecer vazio.
* Nenhuma maquina aparece ate que um agente realize check-in.

Isso e esperado no estado atual.

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
