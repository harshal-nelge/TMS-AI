"""
Vector store manager using ChromaDB with Mistral embeddings
"""
import logging
from typing import List, Optional
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_mistralai import MistralAIEmbeddings

from config.settings import settings
from utils.retry_utils import retry_on_api_error

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """Manages vector storage and retrieval using ChromaDB"""
    
    def __init__(self):
        """Initialize vector store with Mistral embeddings"""
        self.embeddings = self._initialize_embeddings()
        self.persist_directory = settings.CHROMA_PERSIST_DIR
    
    @retry_on_api_error
    def _initialize_embeddings(self) -> MistralAIEmbeddings:
        """
        Initialize Mistral embeddings with retry mechanism
        
        Returns:
            MistralAIEmbeddings instance
        """
        try:
            embeddings = MistralAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                mistral_api_key=settings.MISTRAL_API_KEY
            )
            logger.info("Mistral embeddings initialized successfully")
            return embeddings
        except Exception as e:
            logger.error(f"Error initializing embeddings: {str(e)}")
            raise
    
    @retry_on_api_error
    def create_vector_store(self, chunks: List[Document], collection_name: str) -> Chroma:
        """
        Create vector store from document chunks with retry mechanism
        
        Args:
            chunks: List of document chunks
            collection_name: Name for the ChromaDB collection
            
        Returns:
            Chroma vector store instance
        """
        try:
            logger.info(f"Creating vector store for collection: {collection_name}")
            
            vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                collection_name=collection_name,
                persist_directory=self.persist_directory
            )
            
            # Persist the vector store
            vector_store.persist()
            
            logger.info(f"Vector store created with {len(chunks)} chunks")
            return vector_store
            
        except Exception as e:
            logger.error(f"Error creating vector store: {str(e)}")
            raise
    
    def load_vector_store(self, collection_name: str) -> Optional[Chroma]:
        """
        Load existing vector store
        
        Args:
            collection_name: Name of the collection to load
            
        Returns:
            Chroma vector store instance or None if not found
        """
        try:
            vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            logger.info(f"Loaded vector store for collection: {collection_name}")
            return vector_store
            
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            return None
    
    @retry_on_api_error
    def similarity_search(
        self, 
        vector_store: Chroma, 
        query: str, 
        k: int = None
    ) -> List[tuple]:
        """
        Perform similarity search with scores and retry mechanism
        
        Args:
            vector_store: Chroma vector store instance
            query: Search query
            k: Number of results to return (default from settings)
            
        Returns:
            List of (Document, score) tuples
        """
        if k is None:
            k = settings.TOP_K_RETRIEVAL
        
        try:
            results = vector_store.similarity_search_with_score(query, k=k)
            logger.info(f"Retrieved {len(results)} chunks for query")
            return results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            raise
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection from ChromaDB
        
        Args:
            collection_name: Name of collection to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            vector_store = self.load_vector_store(collection_name)
            if vector_store:
                vector_store.delete_collection()
                logger.info(f"Deleted collection: {collection_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            return False
