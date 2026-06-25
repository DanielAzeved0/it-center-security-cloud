# Backend

API do IT Center Security Cloud construída com Python e FastAPI.

## Requisitos

```text
Python 3.14+
```

## Configuração local

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Execução

```powershell
$env:AGENT_API_KEY="change-me"
$env:DATABASE_URL="postgresql://itcenter:change-me@127.0.0.1:5432/it_center_security_cloud"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check:

```text
GET http://127.0.0.1:8000/api/v1/health
```
