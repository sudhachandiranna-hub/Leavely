FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend backend

EXPOSE 8000

# Render assigns its own PORT (default 10000) and expects the app to bind to it;
# fall back to 8000 for local/other hosts that don't set PORT.
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
