#!/bin/bash

# Start FastAPI backend on port 8000
echo "Starting FastAPI backend on port 8000..."
uvicorn app:app --host 0.0.0.0 --port 8000
