#!/bin/bash
uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir backend &

until curl -sf http://localhost:8000/health > /dev/null; do
  sleep 2
done

FRONTEND_URL=http://localhost:${PORT} API_URL=http://localhost:8000 streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0
