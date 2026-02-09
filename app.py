"""
TMS AI - FastAPI Application
Transportation Management System AI Assistant for Document Processing
"""
import os
import logging
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import shutil

from config.settings import settings
from models.schemas import (
    UploadResponse, AskRequest, AskResponse, 
    ExtractResponse, ErrorResponse, SourceChunk
)
from modules.document_processor import DocumentProcessor
from modules.vector_store import VectorStoreManager
from modules.rag_engine import RAGEngine
from modules.extractor import StructuredExtractor
from utils.helpers import (
    generate_document_id, validate_file_extension, 
    validate_file_size, format_error_message
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TMS AI Document Processing",
    description="AI-powered logistics document processing and question answering system",
    version="1.0.0"
)

# Add CORS middleware for Streamlit integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize modules
try:
    settings.validate()
    document_processor = DocumentProcessor()
    vector_store_manager = VectorStoreManager()
    rag_engine = RAGEngine()
    extractor = StructuredExtractor()
    logger.info("All modules initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize modules: {str(e)}")
    raise

# In-memory document tracking
document_registry = {}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "TMS AI Document Processing API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload",
            "ask": "/ask",
            "extract": "/extract"
        },
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a logistics document
    
    Accepts: PDF, DOCX, TXT files
    Returns: Document ID for future queries
    """
    try:
        # Validate file extension
        if not validate_file_extension(file.filename, settings.ALLOWED_EXTENSIONS):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content to check size
        content = await file.read()
        if not validate_file_size(len(content), settings.MAX_FILE_SIZE):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Max size: {settings.MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        # Generate document ID
        document_id = generate_document_id()
        
        # Save uploaded file
        file_path = os.path.join(settings.UPLOAD_DIR, f"{document_id}_{file.filename}")
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved file: {file_path}")
        
        # Process document
        chunks = document_processor.process_document(file_path, document_id)
        
        # Create vector store
        collection_name = f"doc_{document_id}"
        vector_store = vector_store_manager.create_vector_store(chunks, collection_name)
        
        # Register document
        document_registry[document_id] = {
            "filename": file.filename,
            "file_path": file_path,
            "collection_name": collection_name,
            "num_chunks": len(chunks)
        }
        
        logger.info(f"Document {document_id} processed successfully with {len(chunks)} chunks")
        
        return UploadResponse(
            success=True,
            document_id=document_id,
            filename=file.filename,
            message="Document uploaded and processed successfully",
            num_chunks=len(chunks)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Ask a question about an uploaded document
    
    Uses RAG to retrieve relevant context and generate grounded answers
    Returns answer with confidence score and source citations
    """
    try:
        # Check if document exists
        if request.document_id not in document_registry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found. Please upload the document first."
            )
        
        doc_info = document_registry[request.document_id]
        collection_name = doc_info["collection_name"]
        
        # Load vector store
        vector_store = vector_store_manager.load_vector_store(collection_name)
        
        if not vector_store:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load document vector store"
            )
        
        logger.info(f"Processing question for document {request.document_id}: {request.question}")
        
        # Get answer using RAG
        result = rag_engine.ask_question(vector_store, request.question)
        
        # Format sources
        sources = [
            SourceChunk(
                content=source["content"],
                similarity_score=source["similarity_score"],
                metadata=source["metadata"]
            )
            for source in result["sources"]
        ]
        
        return AskResponse(
            success=True,
            answer=result["answer"],
            confidence_score=result["confidence_score"],
            confidence_category=result["confidence_category"],
            sources=sources
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in ask endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        )

@app.post("/extract", response_model=ExtractResponse)
async def extract_structured_data(document_id: str):
    """
    Extract structured shipment data from document
    
    Returns JSON with shipment fields (nulls for missing data)
    """
    try:
        # Check if document exists
        if document_id not in document_registry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found. Please upload the document first."
            )
        
        doc_info = document_registry[document_id]
        collection_name = doc_info["collection_name"]
        
        # Load vector store
        vector_store = vector_store_manager.load_vector_store(collection_name)
        
        if not vector_store:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load document vector store"
            )
        
        logger.info(f"Extracting structured data from document {document_id}")
        
        # Extract shipment data
        shipment_data = extractor.extract_shipment_data(vector_store, document_id)
        
        return ExtractResponse(
            success=True,
            document_id=document_id,
            shipment_data=shipment_data,
            message="Structured data extracted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in extract endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting data: {str(e)}"
        )

@app.delete("/document/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its vector store"""
    try:
        if document_id not in document_registry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        doc_info = document_registry[document_id]
        
        # Delete file
        if os.path.exists(doc_info["file_path"]):
            os.remove(doc_info["file_path"])
        
        # Delete vector store collection
        vector_store_manager.delete_collection(doc_info["collection_name"])
        
        # Remove from registry
        del document_registry[document_id]
        
        logger.info(f"Deleted document {document_id}")
        
        return {"success": True, "message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
