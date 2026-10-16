FROM python:3.11-slim

WORKDIR /app
COPY backend/requirements.lock ./backend/requirements.lock
RUN python -m pip install --no-cache-dir -r backend/requirements.lock
COPY backend ./backend

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
