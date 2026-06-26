# SECURITY.md

# Política de Segurança

## Objetivo

Garantir que o IT Center Security Cloud seja desenvolvido seguindo princípios de segurança desde o início.

---

# Princípios

## Menor Privilégio

Cada componente deve possuir apenas as permissões necessárias.

---

## Criptografia

Todo tráfego externo deve utilizar HTTPS.

---

## Segredos

Nunca armazenar:

* Senhas
* Tokens
* Chaves

Dentro do código-fonte.

Utilizar:

.env

---

## Auditoria

Toda ação crítica deverá gerar logs.

---

## Proteção da API

MVP:

* API Key obrigatória para agentes
* Validação de payloads
* Erros sem detalhes internos

Futuro:

* JWT
* RBAC
* Rate limit
* Logs de auditoria completos

---

## Proteção do Banco

* Acesso apenas interno
* Sem exposição pública
* Backups automáticos

---

## Segurança do Agente

* Comunicação HTTPS
* API Key obrigatória
* Header oficial: X-Agent-Api-Key
* Validação de payload
* Cache offline sem dados sensíveis

---

## Segurança do Dashboard

MVP local/laboratório:

* Pode operar sem login apenas enquanto não estiver exposto na internet

Antes de exposição externa:

* O Nginx exige autenticação HTTP Basic para todo o dashboard e para a proxy interna `/api/backend/*`.
* O arquivo de credenciais fica em `.secrets/dashboard.htpasswd`, fora do Git e montado somente em leitura.
* O endpoint público do agente é limitado a `POST /api/v1/agent/checkin`; ele não recebe Basic Auth porque valida obrigatoriamente `X-Agent-Api-Key` no FastAPI.
* Endpoints internos do backend não são expostos em portas públicas.

Limitação conhecida:

* HTTP Basic é o controle de acesso administrativo mínimo para a primeira publicação. Login com usuários, sessões, RBAC e auditoria continua sendo requisito da Fase de Governança antes de qualquer uso multiusuário/SaaS.

---

# Requisitos Obrigatórios

Não serão aceitos:

* Senhas em texto plano
* Secrets no GitHub
* Banco exposto na internet
* HTTP sem TLS
* Check-in de agente sem API Key

---

# Varredura de Imagens e Dependencias

## Objetivo

Evitar que imagens Docker com vulnerabilidades criticas ou altas sejam promovidas para ambiente publicado.

## Ferramenta Padrao

Docker Scout.

Comandos obrigatorios antes de publicar uma nova imagem:

```powershell
docker scout cves postgres:16-alpine --only-severity critical,high
docker scout cves infra-backend:latest --only-severity critical,high
docker scout cves infra-frontend:latest --only-severity critical,high
```

Para investigar caminho de correcao:

```powershell
docker scout recommendations postgres:16-alpine
docker scout recommendations infra-backend:latest
docker scout recommendations infra-frontend:latest
```

## Prioridade

P0:

* Vulnerabilidade critica ou alta com pacote usado em runtime pelo backend ou frontend.
* Vulnerabilidade com exploracao remota sem autenticacao.
* Vulnerabilidade em componente exposto externamente.

P1:

* Vulnerabilidade critica ou alta em imagem oficial sem versao corrigida disponivel.
* Vulnerabilidade em pacote empacotado por framework quando nao existe versao upstream corrigida.
* Vulnerabilidade em dependencia indireta sem impacto claro no fluxo atual.

P2:

* Vulnerabilidades medias ou baixas.
* Alertas em ferramentas de desenvolvimento que nao entram na imagem final.

## Politica de Correcao

* Atualizar dependencias diretas para versoes corrigidas.
* Atualizar imagem base quando a recomendacao reduzir CVEs sem quebrar runtime.
* Nao usar `npm audit fix --force` sem revisao, porque pode trocar major versions e quebrar o dashboard.
* Nao ignorar vulnerabilidade critica ou alta sem registrar motivo em `docs/DECISIONS.md`.

## Estado Atual das Imagens

Backend:

* Base alterada para `python:3.14-alpine`.
* Resultado esperado no Docker Scout: zero vulnerabilidades critical/high.

Frontend:

* Next.js atualizado para `16.2.9`.
* `picomatch` fixado em `4.0.4`.
* O build executa `scripts/security/patch-next-picomatch.js` para substituir o `picomatch` compilado dentro do Next por `4.0.4`.
* A imagem final remove o `npm` global do runtime para evitar dependencias internas nao usadas, incluindo `picomatch` vulneravel empacotado pelo npm da imagem base.

PostgreSQL:

* Imagem oficial mantida em `postgres:16-alpine`.
* Se o Scout ainda apontar CVE em `golang/stdlib`, tratar como risco residual P1 enquanto nao houver tag oficial corrigida.
* O banco deve continuar sem exposicao externa e acessivel apenas pela rede Docker/host local controlado.
