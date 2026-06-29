# Known Issues

## API key do agente exposta durante suporte

Estado:

```text
Aberto
```

Impacto:

* Qualquer pessoa com a chave poderia tentar enviar check-ins para o endpoint do agente.

Acao:

* Rotacionar `AGENT_API_KEY` apos concluir a fase de testes.
* Reinstalar ou atualizar os agentes com a nova chave.
* Confirmar `POST /api/v1/agent/checkin` com `200 OK`.

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
