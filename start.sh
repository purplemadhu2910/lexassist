#!/bin/bash
uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir backend &

until python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" 2>/dev/null; do
  sleep 2
done

API_URL=http://localhost:8000 streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0
