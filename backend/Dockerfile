# Python 3.13 is enough for the current FastAPI/psycopg stack and keeps the
# runtime on a stable, small Alpine base.
FROM python:3.13-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies before copying application code to keep Docker cache
# effective when only source files change.
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt \
    && addgroup -S app \
    && adduser -S app -G app

# Copy only runtime files required by the API and migration runner.
COPY app ./app
COPY migrations ./migrations
COPY apply_migrations.py .

EXPOSE 8000

USER app

CMD ["sh", "-c", "python apply_migrations.py && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
