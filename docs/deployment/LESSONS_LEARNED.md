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

Enquanto o Windows Agent nao envia check-ins, o dashboard pode estar vazio. Isso e estado esperado do produto, nao erro de infraestrutura.
