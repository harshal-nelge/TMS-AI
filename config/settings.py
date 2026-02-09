"""
Configuration settings for TMS AI application
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application configuration settings"""
    
    # API Keys
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Document Processing
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # RAG Configuration
    SIMILARITY_THRESHOLD: float = 0.2
    TOP_K_RETRIEVAL: int = 3
    
    # Confidence Scoring Weights
    SIMILARITY_WEIGHT: float = 0.5
    AGREEMENT_WEIGHT: float = 0.5
    
    # Retry Configuration
    MAX_RETRIES: int = 3
    RETRY_MIN_WAIT: int = 1  # seconds
    RETRY_MAX_WAIT: int = 10  # seconds
    
    # Storage Paths
    UPLOAD_DIR: str = "uploads"
    CHROMA_PERSIST_DIR: str = "chroma_db"
    
    # LLM Configuration
    LLM_MODEL: str = "llama-3.1-8b-instant"
    LLM_TEMPERATURE: float = 0.0
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = "mistral-embed"
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: set = {"pdf", "docx", "txt"}
    
    # Server Configuration
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    
    def validate(self):
        """Validate that required API keys are present"""
        if not self.MISTRAL_API_KEY:
            raise ValueError("MISTRAL_API_KEY not found in environment variables")
        if not self.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        # Create necessary directories
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.CHROMA_PERSIST_DIR, exist_ok=True)

# Global settings instance
settings = Settings()
