# Lessons Learned

## 1. Preflight reduz erro operacional

Validar Docker, Compose, secrets, dominio, TLS, portas e recursos antes do deploy evita ciclos longos de tentativa e erro.

## 2. DNS precisa ser testado com mais de um resolver

Um dominio pode estar correto em resolvers publicos e ainda falhar no provedor local.

Boas praticas:

```bash
dig @8.8.8.8 dominio
dig @1.1.1.1 dominio
dig @9.9.9.9 dominio
```

## 3. Permissao de secrets e parte do deploy

Arquivos como `dashboard.htpasswd` precisam de permissao correta. Um erro simples de permissao pode derrubar o Nginx ou impedir autenticacao.

## 4. Swap e importante em VM pequena

VMs gratuitas podem ter memoria limitada. Swap ajuda a estabilizar build e containers, mas nao substitui dimensionamento adequado.

## 5. Healthcheck precisa refletir o runtime real

O healthcheck do frontend precisou ser ajustado porque o Next.js nao respondia corretamente no alvo inicial.

Licao:

* Validar healthchecks de dentro do container.
* Nao assumir que `127.0.0.1` funciona igual em todos os contextos.

## 6. Separar preparacao do host e deploy da aplicacao melhora manutencao

Host, Docker, secrets, TLS e Compose sao camadas diferentes.

Documentar cada camada deixa o projeto mais facil de recriar e explicar.

## 7. Logs em stdout/stderr simplificam observabilidade futura

Manter logs nos containers via stdout/stderr permite evoluir para Loki/Promtail sem mudar a aplicacao.

## 8. Dashboard vazio nao significa falha

Enquanto nenhum Windows Agent envia check-ins, o dashboard pode estar vazio. Isso e estado esperado do produto, nao erro de infraestrutura.

## 9. O instalador do agente deve falhar cedo

Instalar o agente sem validar DNS, porta e health check desperdicou tempo: a tarefa agendada ficava ativa, mas os check-ins acumulavam em cache.

Licao:

* Validar DNS antes de instalar.
* Validar porta 443 antes de instalar.
* Validar `/healthz` antes de instalar.
* Permitir bypass apenas quando a instalacao offline for intencional.

## 10. `hosts` e workaround, nao estrategia

Editar `C:\Windows\System32\drivers\etc\hosts` resolveu um PC especifico, mas nao escala para todas as maquinas monitoradas.

Licao:

* Corrigir DNS no roteador/DHCP.
* Usar DNS confiavel, como Cloudflare ou Google.
* Considerar dominio proprio gerenciado por Cloudflare para o endpoint dos agentes.

## 11. Secrets expostos em operacao devem ser rotacionados

Durante diagnosticos, e facil colar API keys ou senhas em chats e terminais.

Licao:

* Nao documentar valores reais.
* Rotacionar `AGENT_API_KEY` e senha do dashboard apos fases de teste assistido.
* Usar placeholders nos docs.
