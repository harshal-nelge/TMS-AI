#!/bin/bash

# Start FastAPI in the background
echo "Starting FastAPI backend on port 8000..."
uvicorn app:app --host 0.0.0.0 --port 8000 &

# Wait for FastAPI to start
sleep 3

# Start Streamlit on port 8501
echo "Starting Streamlit UI on port 8501..."
streamlit run ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
