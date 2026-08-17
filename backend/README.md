# Backend

API do IT Center Security Cloud construida com Python e FastAPI.

## Execucao recomendada

Use o Docker Compose da raiz do projeto:

```powershell
docker compose -f infra/docker-compose.yml up --build
```

O container do backend:

```text
1. Instala as dependencias da imagem.
2. Executa python apply_migrations.py.
3. Inicia uvicorn app.main:app em 0.0.0.0:8000.
```

Health check:

```text
GET http://127.0.0.1:8000/api/v1/health
```

## Arquivos de runtime

```text
backend/Dockerfile
backend/apply_migrations.py
backend/migrations/
backend/requirements.txt
```

## Variaveis

```text
AGENT_API_KEY
DATABASE_URL
AUTH_TOKEN_SECRET
AUTH_TOKEN_EXPIRATION_MINUTES
APP_ENV
```

No Docker Compose, `DATABASE_URL` aponta para o servico interno `postgres`.

Quando `APP_ENV=production`, o startup da API roda `validate_runtime_configuration` (`app/core/config.py`) e falha rapido (`RuntimeError`) se `AGENT_API_KEY`, `AUTH_TOKEN_SECRET` ou `DATABASE_URL` ainda estiverem com valor padrao/inseguro (`change-me`, vazio, etc.), evitando subir em produção com credenciais de exemplo.

Tambem quando `APP_ENV=production`, `app/main.py` desativa `docs_url`/`redoc_url`/`openapi_url` (`/docs`, `/redoc`, `/openapi.json` respondem `404`) — defesa em profundidade contra qualquer bypass de path traversal no proxy do dashboard que consiga alcancar esses caminhos diretamente (EPIC 28).

## Execucao manual

Use apenas quando precisar depurar fora do container.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Aplicar migrations:

```powershell
python apply_migrations.py
```

Subir API:

```powershell
$env:AGENT_API_KEY="change-me"
$env:DATABASE_URL="postgresql://itcenter:change-me@127.0.0.1:5432/it_center_security_cloud"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
