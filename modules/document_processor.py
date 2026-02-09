"""
Document processing module for parsing and chunking logistics documents
"""
import os
import logging
from typing import List, Dict, Any
from pathlib import Path

# Document loaders
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from config.settings import settings

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Handles document parsing and intelligent chunking"""
    
    def __init__(self):
        """Initialize document processor with text splitter"""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
    
    def load_document(self, file_path: str) -> List[Document]:
        """
        Load document based on file extension
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of Document objects
            
        Raises:
            ValueError: If file type is not supported
        """
        file_extension = Path(file_path).suffix.lower()
        
        try:
            if file_extension == '.pdf':
                loader = PyPDFLoader(file_path)
            elif file_extension == '.docx':
                loader = Docx2txtLoader(file_path)
            elif file_extension == '.txt':
                loader = TextLoader(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} pages from {file_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            raise
    
    def chunk_documents(self, documents: List[Document], document_id: str, filename: str) -> List[Document]:
        """
        Split documents into intelligent chunks with metadata
        
        Args:
            documents: List of Document objects
            document_id: Unique identifier for the document
            filename: Original filename
            
        Returns:
            List of chunked Document objects with metadata
        """
        try:
            # Split documents into chunks
            chunks = self.text_splitter.split_documents(documents)
            
            # Add metadata to each chunk
            for idx, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_index": idx,
                    "total_chunks": len(chunks)
                })
            
            logger.info(f"Created {len(chunks)} chunks from document {filename}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking documents: {str(e)}")
            raise
    
    def process_document(self, file_path: str, document_id: str) -> List[Document]:
        """
        Complete document processing pipeline
        
        Args:
            file_path: Path to the document
            document_id: Unique identifier
            
        Returns:
            List of processed chunks with metadata
        """
        filename = os.path.basename(file_path)
        
        # Load document
        documents = self.load_document(file_path)
        
        # Chunk documents
        chunks = self.chunk_documents(documents, document_id, filename)
        
        return chunks
    
    def get_document_stats(self, chunks: List[Document]) -> Dict[str, Any]:
        """
        Get statistics about processed document
        
        Args:
            chunks: List of document chunks
            
        Returns:
            Dictionary with document statistics
        """
        total_chars = sum(len(chunk.page_content) for chunk in chunks)
        
        stats = {
            "num_chunks": len(chunks),
            "total_characters": total_chars,
            "avg_chunk_size": total_chars // len(chunks) if chunks else 0,
            "metadata_sample": chunks[0].metadata if chunks else {}
        }
        
        return stats
