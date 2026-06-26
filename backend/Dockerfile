FROM python:3.14-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY migrations ./migrations
COPY apply_migrations.py .

EXPOSE 8000

CMD ["sh", "-c", "python apply_migrations.py && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
