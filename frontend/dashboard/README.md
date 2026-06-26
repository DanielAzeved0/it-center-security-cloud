# Dashboard

Dashboard web do IT Center Security Cloud construido com Next.js e TypeScript.

## Execucao recomendada

Use o Docker Compose da raiz do projeto:

```powershell
docker compose -f infra/docker-compose.yml up --build
```

URL local:

```text
http://127.0.0.1:3000
```

No Docker Compose, o dashboard aponta para o backend pelo DNS interno:

```text
ITCENTER_API_BASE_URL=http://backend:8000
```

## Requisitos para execucao manual

```text
Node.js 25+
npm
Backend FastAPI em execucao
```

## Configuracao

O dashboard usa um proxy interno em:

```text
/api/backend/...
```

Por padrao, o proxy aponta para:

```text
http://127.0.0.1:8000
```

Para alterar:

```powershell
$env:ITCENTER_API_BASE_URL="http://127.0.0.1:8000"
```

## Execucao manual

```powershell
cd frontend/dashboard
npm install
npm run dev
```

URL local:

```text
http://127.0.0.1:3000
```

## Telas

```text
/          Dashboard operacional
/machines  Inventario, metricas e programas
/alerts    Alertas e acao de resolver
/security  Eventos de seguranca
```

## Seguranca de dependencias

O dashboard usa Next.js `16.2.9` e `picomatch` `4.0.4`.

Durante o build Docker, o script abaixo substitui o `picomatch` compilado dentro do Next.js pela versao corrigida instalada no projeto:

```text
scripts/security/patch-next-picomatch.js
```

Esse script roda antes de `npm run build` no `Dockerfile`.

A imagem final roda o Next.js diretamente com `node` e remove o `npm` global da camada de runtime. Isso evita carregar dependencias internas do npm que nao sao necessarias para executar o dashboard e podem aparecer no Docker Scout.

Validacao recomendada apos build da imagem:

```powershell
docker scout cves infra-frontend:latest --only-severity critical,high
```
