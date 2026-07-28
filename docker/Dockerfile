FROM python:3.12.11-slim-bookworm AS runtime

ARG APP_MODULE
ARG APP_PORT=8000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_MODULE=${APP_MODULE} \
    PORT=${APP_PORT}

WORKDIR /app

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /nonexistent app

COPY requirements.txt .
RUN python -m pip install --upgrade pip==25.1.1 \
    && python -m pip install --requirement requirements.txt

COPY platform_core ./platform_core
COPY services ./services
COPY aiops ./aiops

USER 10001:10001
EXPOSE ${APP_PORT}

HEALTHCHECK --interval=20s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/health/live', timeout=2)"

CMD ["sh", "-c", "exec uvicorn \"$APP_MODULE\" --host 0.0.0.0 --port \"$PORT\" --no-access-log"]
