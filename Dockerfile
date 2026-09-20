FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --upgrade pip && pip install -r ./backend/requirements.txt

COPY backend ./backend
COPY frontend ./frontend

EXPOSE 8000 8081

CMD ["python", "/app/backend/agent.py", "start"]
