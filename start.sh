#!/bin/bash

# Start FastAPI backend on port 8001 (internal)
echo "Starting FastAPI backend on port 8001..."
uvicorn app:app --host 0.0.0.0 --port 8001 &

# Start Streamlit UI on port 8002 (internal)
echo "Starting Streamlit UI on port 8002..."
streamlit run ui/streamlit_app.py --server.port 8002 --server.address 0.0.0.0 --server.headless true &

# Wait for services to start
sleep 5

# Start reverse proxy on port 8000 (public-facing)
echo "Starting reverse proxy on port 8000..."
python proxy.py
