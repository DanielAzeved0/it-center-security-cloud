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
/login     Login administrativo (Bearer token, RBAC)
/          Dashboard operacional
/executive Dashboard executivo (resumo agregado + exportar PDF)
/machines  Inventario, metricas e programas
/alerts    Alertas e acao de resolver
/security  Eventos de seguranca
```

Em `/executive` e no detalhe de maquina (`/machines/[id]`), o botao "Exportar PDF" baixa um relatorio gerado pelo backend (`reportlab`) via `GET /api/v1/reports/executive.pdf` e `GET /api/v1/machines/{id}/report.pdf`.

## Seguranca de dependencias

O dashboard usa Next.js `16.2.12`, `picomatch` `4.0.4` e `overrides` de `postcss`/`sharp` (`8.5.25`/`0.35.3`) em `package.json` para fechar CVEs high de dependencias internas do Next que a versao atual ainda nao corrigiu.

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
