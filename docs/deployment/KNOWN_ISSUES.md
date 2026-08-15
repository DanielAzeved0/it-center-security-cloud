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

## Chave SSH pessoal sem copia de backup

Acesso administrativo a `itcenter-edge-01` depende de uma unica chave SSH pessoal.

Risco:

* Perda da chave bloqueia todo acesso administrativo (backup/restore/rollback/TLS, credenciais do dashboard) ate uma recuperacao de emergencia. Ja aconteceu em producao **duas vezes**: INCIDENTE 018 (`POSTMORTEMS.md`, 2026-07-28, com exposicao acidental de uma chave privada durante a recuperacao), e novamente em 2026-08-15 durante a tentativa de retomar a EPIC 15 (state remoto do Terraform) — mesmo workflow de recuperacao reaplicado com sucesso, sem repetir o erro anterior (so a chave publica nova foi compartilhada).

Mitigacao atual:

* Workflow `workflow_dispatch` reaproveitando o secret `PROD_SSH_PRIVATE_KEY` ja usado pelo deploy, como recuperacao de ultimo recurso — removido do repositorio logo apos o uso (repetido em ambas as ocorrencias).

Evolucao esperada:

* Guardar uma copia de recuperacao da chave SSH pessoal em um cofre de senhas — ainda nao feito, mesma lacuna das duas ocorrencias.
* Documentar acesso alternativo via OCI Console/Serial Console como plano B.

## Acesso ao Console Oracle Cloud bloqueado (MFA do administrador perdido)

Descoberto em 2026-08-15 ao tentar retomar a EPIC 15 (migracao do state do Terraform para backend remoto): o unico usuario administrador da tenancy Oracle Cloud perdeu o segundo fator de autenticacao (MFA vinculado a um celular antigo), sem fator de backup configurado e sem um segundo usuario administrador na conta.

Contexto adicional descoberto na mesma investigacao: o `terraform.tfvars` e o `terraform.tfstate` reais do import de 2026-08-04 (EPIC 15) tambem nao foram localizados — nao estao em `itcenter-edge-01` nem em copia conhecida. A API key do usuario IAM `terraform-provisioner` (criada na mesma epoca) tambem foi dada como perdida.

Risco:

* **Nenhuma acao no Console ou via `oci` CLI e possivel** ate a conta ser recuperada: criar/rotacionar API keys, criar o bucket de Object Storage para o state remoto, ou qualquer recriacao de emergencia da VM ou da rede (cenario de disaster recovery da EPIC 15/IAC.md).
* A aplicacao em si (dashboard, backend, agente, Nginx) continua funcionando normalmente — o bloqueio e apenas para operacoes administrativas de infraestrutura na nuvem.
* Combinado com o item acima (chave SSH), a operacao do projeto hoje depende inteiramente do acesso SSH continuo a VM — sem plano B caso a VM precise ser recriada do zero.

Mitigacao atual:

* Nenhuma — bloqueio em aberto.

Evolucao esperada (bloqueante para fechar a EPIC 15):

* Recuperar o acesso ao Console OCI (fator de backup na tela de login, um segundo administrador existente, ou Service Request com o suporte Oracle provando titularidade da tenancy).
* Apos recuperado: cadastrar um segundo usuario administrador e um fator de MFA de backup, para nao repetir esse bloqueio.
* Gerar uma API key nova para `terraform-provisioner` e refazer a descoberta/import do Terraform do zero (`infra/terraform/README.md`), ja que o state de 2026-08-04 nao foi localizado.
* So depois disso retomar os itens pendentes da EPIC 15 (bucket de state remoto e `terraform init -migrate-state`).

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

## Basic Auth no Nginx: reavaliar necessidade

O Nginx aplica Basic Auth via cabecalho `Authorization: Basic ...`. Qualquer rota que o dashboard chame usando `Authorization: Bearer <token>` perde a credencial Basic Auth do ponto de vista do Nginx, pois o HTTP so permite um `Authorization` por requisicao.

Mitigacao atual:

* Rotas de API chamadas pela SPA com Bearer token (`/api/backend/`) sao isentas de `auth_basic` no Nginx (ADR-023), protegidas apenas pelo RBAC/token da aplicacao.

Risco:

* Qualquer nova rota publica adicionada sob `location /` que tambem exija Bearer token reproduzira o mesmo loop de login (INCIDENTE 020 em `POSTMORTEMS.md`) se nao for isenta de Basic Auth da mesma forma.

Pendencia real (ADR-023):

* O login administrativo completo (usuarios, sessoes, RBAC e auditoria — ADR-021, ADR-022, `docs/security/AUTH.md`) ja esta em producao. O Basic Auth do Nginx continua sendo apenas uma camada adicional do MVP; sua real necessidade deve ser reavaliada agora que esse login existe, em vez de tratado como controle administrativo definitivo.

## Auditoria de dependencias do frontend bloqueada no ambiente de desenvolvimento

Durante a auditoria de seguranca do frontend em 2026-07-29, `npm audit` em `frontend/dashboard/` falhou com `self-signed certificate in certificate chain` ao tentar acessar `registry.npmjs.org` a partir do ambiente de desenvolvimento atual (proxy corporativo intercepta TLS).

Risco:

* Nao ha confirmacao automatizada de CVEs em `next@16.2.12`/`react@19.2.3` e demais dependencias diretas do dashboard a partir do ambiente de desenvolvimento local, alem do que o Docker Scout ja cobre na imagem final (ver `docs/security/SECURITY.md`).

Mitigacao atual:

* `docker scout cves infra-frontend:latest --only-severity critical,high` continua sendo a validacao oficial antes de publicar a imagem (ja documentado em `docs/security/SECURITY.md`).
* O passo `Audit frontend dependencies` do workflow `ci.yml` (GitHub Actions, sem o proxy corporativo local) roda `npm audit --audit-level=high` a cada push/PR e ja provou seu valor em 2026-08-03: pegou 3 CVEs high reais em `next@16.2.9` (bypass de middleware/proxy, SSRF em rewrites, DoS em Server Actions) e mais duas em dependencias internas do Next (`postcss`, `sharp`). Corrigido com bump para `next@16.2.12` e `overrides` de `postcss`/`sharp` em `package.json` (ver `docs/security/SECURITY.md`).

Evolucao esperada:

* Se for necessario rodar `npm audit`/`npm install` localmente antes de abrir PR, o bloqueio de TLS pode ser contornado pontualmente exportando a cadeia de certificado do proxy/antivirus (`openssl s_client -connect registry.npmjs.org:443 -showcerts`) e apontando `NODE_EXTRA_CA_CERTS` para esse arquivo — nao adicionar isso como configuracao permanente do repositorio nem desabilitar `strict-ssl`.

## `npm run lint` quebrado no frontend

Descoberto em 2026-08-04 durante a implementacao da EPIC 19: `npm run lint` (`next lint`) falha em `frontend/dashboard/`.

Causa:

```text
Next.js 16 removeu o comando integrado `next lint` (substituido por ESLint standalone) e o projeto nunca teve `eslint` como devDependency — nao e uma regressao da EPIC 19, o mesmo erro ja ocorria antes dessa mudanca (reproduzido isoladamente com `npx next lint .`).
```

Risco:

* O passo de lint documentado em `CLAUDE.md` ("Frontend: `npm run lint` e `npm run build`") nao funciona hoje; `npm run build` (TypeScript + Next) continua sendo a unica verificacao automatizada real do frontend fora do CI.

Evolucao esperada:

* Adicionar `eslint`/`eslint-config-next` como devDependency e migrar para o CLI standalone do ESLint, em tarefa propria (fora do escopo da EPIC 19).

## PostgreSQL no mesmo Edge Node

No MVP, PostgreSQL roda no mesmo host por custo zero.

Risco:

* Nao ha alta disponibilidade.

Evolucao futura:

* Instancia privada dedicada.
* Banco gerenciado.
* Backups automatizados externos.
