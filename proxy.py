"""
Reverse Proxy Server for TMS AI
Handles routing for both FastAPI backend and Streamlit UI on a single port
"""
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, Response
import httpx
import uvicorn

app = FastAPI(title="TMS AI Proxy")

# Backend services
FASTAPI_URL = "http://localhost:8001"
STREAMLIT_URL = "http://localhost:8002"

@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_api(path: str, request: Request):
    """Proxy all /api/* requests to FastAPI backend"""
    client = httpx.AsyncClient()
    url = f"{FASTAPI_URL}/{path}"
    
    # Get query parameters
    query_params = dict(request.query_params)
    
    # Get headers (excluding host)
    headers = dict(request.headers)
    headers.pop("host", None)
    
    # Get body if present
    body = await request.body()
    
    try:
        response = await client.request(
            method=request.method,
            url=url,
            params=query_params,
            headers=headers,
            content=body,
            timeout=300.0
        )
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    finally:
        await client.aclose()

@app.api_route("/ui/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_ui(path: str, request: Request):
    """Proxy all /ui/* requests to Streamlit"""
    client = httpx.AsyncClient()
    url = f"{STREAMLIT_URL}/{path}"
    
    query_params = dict(request.query_params)
    headers = dict(request.headers)
    headers.pop("host", None)
    body = await request.body()
    
    try:
        response = await client.request(
            method=request.method,
            url=url,
            params=query_params,
            headers=headers,
            content=body,
            timeout=300.0
        )
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    finally:
        await client.aclose()

@app.get("/ui")
async def proxy_ui_root(request: Request):
    """Proxy /ui to Streamlit root"""
    client = httpx.AsyncClient()
    
    headers = dict(request.headers)
    headers.pop("host", None)
    
    try:
        response = await client.get(
            STREAMLIT_URL,
            headers=headers,
            timeout=300.0
        )
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    finally:
        await client.aclose()

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "name": "TMS AI Service",
        "version": "1.0.0",
        "services": {
            "api": "/api",
            "ui": "/ui"
        },
        "endpoints": {
            "upload": "/api/upload",
            "ask": "/api/ask",
            "extract": "/api/extract",
            "health": "/api/health"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "proxy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
