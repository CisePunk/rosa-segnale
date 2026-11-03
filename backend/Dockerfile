FROM python:3.12-slim

WORKDIR /app

COPY requirements.lock .
RUN python -m pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.lock

COPY app ./app

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/data /app/reports \
    && chown -R appuser:appuser /app/data /app/reports

ENV TRIAGE_DB_PATH=/app/data/triage.db
ENV REPORTS_DIR=/app/reports

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
