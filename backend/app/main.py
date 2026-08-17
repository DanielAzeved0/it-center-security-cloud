import os

from fastapi import FastAPI

from app.routes.agent import router as agent_router
from app.routes.alerts import router as alerts_router
from app.routes.auth import router as auth_router
from app.routes.dashboard import router as dashboard_router
from app.routes.machines import router as machines_router
from app.routes.reports import router as reports_router
from app.routes.security_events import router as security_events_router

# Mesmo padrao de deteccao dev/producao ja usado em app/core/config.py e
# app/database.py: APP_ENV=production desliga a documentacao interativa da
# API (defesa em profundidade — segunda camada contra qualquer bypass de
# path traversal no proxy que consiga alcancar /docs, /redoc ou
# /openapi.json diretamente).
_IS_PRODUCTION = os.getenv("APP_ENV", "development").lower() == "production"

app = FastAPI(
    title="IT Center Security Cloud API",
    docs_url=None if _IS_PRODUCTION else "/docs",
    redoc_url=None if _IS_PRODUCTION else "/redoc",
    openapi_url=None if _IS_PRODUCTION else "/openapi.json",
)

app.include_router(agent_router)
app.include_router(auth_router)
app.include_router(alerts_router)
app.include_router(machines_router)
app.include_router(security_events_router)
app.include_router(dashboard_router)
app.include_router(reports_router)


@app.on_event("startup")
def validate_runtime_configuration() -> None:
    from app.core.config import get_settings

    get_settings().validate_runtime_configuration()


@app.get("/api/v1/health")
def health():
    return {
        "status": "healthy",
        "service": "it-center-security-cloud",
    }
