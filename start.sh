#!/bin/bash

# Start FastAPI in the background on port 8001
echo "Starting FastAPI backend on port 8001..."
uvicorn app:app --host 0.0.0.0 --port 8001 &

# Wait for FastAPI to start
sleep 3

# Start Streamlit on port 8000
echo "Starting Streamlit UI on port 8000..."
streamlit run ui/streamlit_app.py --server.port 8000 --server.address 0.0.0.0 --server.headless true --server.baseUrlPath /ui
