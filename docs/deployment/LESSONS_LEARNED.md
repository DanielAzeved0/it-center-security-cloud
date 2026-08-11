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

## 11. Acesso administrativo nao pode depender de uma unica chave SSH sem backup

Perder a unica chave SSH pessoal bloqueia todo o acesso administrativo a VM, incluindo backup, restore, rollback e renovacao de TLS.

Licao:

* Guardar copia de recuperacao da chave SSH em um cofre de senhas.
* Documentar um plano B de acesso (ex.: OCI Console/Serial Console) que nao dependa de um unico canal, como o GitHub Actions.

## 12. "Deploy concluido" nao significa "dados iniciais semeados"

Scripts de setup unico (como a criacao do primeiro usuario admin) ficam fora da imagem Docker e fora do `deploy.sh` sao facilmente esquecidos, porque so precisam rodar uma vez.

Licao:

* Incluir o seed de dados iniciais (ex.: primeiro admin) como etapa explicita do checklist de deploy, nao como algo implicito.

## 13. Basic Auth generico conflita com autenticacao propria da aplicacao

O HTTP permite apenas um cabecalho `Authorization` por requisicao. Basic Auth aplicado sem excecao sobre toda a aplicacao quebra qualquer rota que a propria aplicacao proteja com `Authorization: Bearer <token>`.

Licao:

* Isentar de Basic Auth as rotas que ja tem seu proprio esquema de autenticacao (RBAC/token), em vez de aplicar Basic Auth de forma indiscriminada.

## 14. Tag de imagem Docker externa deve ser confirmada antes de fixar no Compose

Uma tag inexistente em um servico que so roda sob profile opcional pode passar despercebida por muito tempo, porque nao aparece em smoke tests nem em deploys de rotina.

Licao:

* Confirmar a existencia da tag via API do registry ou release oficial antes de fixar a versao no Compose, nao apenas assumir.
