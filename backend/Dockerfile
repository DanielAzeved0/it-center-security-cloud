# Python 3.13 is enough for the current FastAPI/psycopg stack and keeps the
# runtime on a stable, small Alpine base.
FROM python:3.13-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# Build context is the repository root (not backend/) so this Dockerfile can also copy the
# signed agent release below - see infra/docker-compose*.yml and EPIC 22 (ADR-032).

# Install dependencies before copying application code to keep Docker cache
# effective when only source files change.
COPY backend/requirements.txt .
# pip/setuptools/wheel are only needed to install the packages above - not to run the app
# afterward. Removed from the final image (mirrors frontend/dashboard/Dockerfile removing
# npm) because pip vendors its own copies of msgpack/setuptools/jaraco.*/wheel internally,
# and those vendored copies keep showing up as CVEs in Docker Scout independent of what
# requirements.txt pins.
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt \
    && python -m pip uninstall --yes pip setuptools wheel \
    && addgroup -S app \
    && adduser -S app -G app

# Copy only runtime files required by the API and migration runner.
COPY backend/app ./app
COPY backend/migrations ./migrations
COPY backend/apply_migrations.py .

# Signed agent release published via GET /api/v1/agent/manifest and GET /api/v1/agent/download
# (EPIC 22, ADR-032). Publishing a new agent version means bumping $script:AgentVersion,
# re-signing with agent-windows/scripts/Sign-AgentScripts.ps1, and redeploying the backend -
# there is no separate release store. See docs/backend/DATABASE.md ("Origem do release do agente").
COPY agent-windows/itcenter-agent.ps1 ./agent-release/itcenter-agent.ps1

EXPOSE 8000

USER app

CMD ["sh", "-c", "python apply_migrations.py && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
