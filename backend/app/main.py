from fastapi import FastAPI

from app.routes.agent import router as agent_router
from app.routes.alerts import router as alerts_router
from app.routes.machines import router as machines_router
from app.routes.security_events import router as security_events_router

app = FastAPI(title="IT Center Security Cloud API")

app.include_router(agent_router)
app.include_router(alerts_router)
app.include_router(machines_router)
app.include_router(security_events_router)


@app.get("/api/v1/health")
def health():
    return {
        "status": "healthy",
        "service": "it-center-security-cloud",
    }
