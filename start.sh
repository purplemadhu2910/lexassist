#!/bin/bash
# Start backend on port 8000 internally
uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir backend &

# Wait for backend to start
sleep 5

# Start frontend on Render's public port
API_URL=http://localhost:8000 streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0
