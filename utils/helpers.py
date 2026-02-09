"""
Helper utility functions
"""
import uuid
from typing import Optional

def generate_document_id() -> str:
    """Generate a unique document ID"""
    return str(uuid.uuid4())

def validate_file_extension(filename: str, allowed_extensions: set) -> bool:
    """
    Validate file extension
    
    Args:
        filename: Name of the file
        allowed_extensions: Set of allowed extensions (without dot)
    
    Returns:
        True if extension is valid, False otherwise
    """
    if '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in allowed_extensions

def validate_file_size(file_size: int, max_size: int) -> bool:
    """
    Validate file size
    
    Args:
        file_size: Size of file in bytes
        max_size: Maximum allowed size in bytes
    
    Returns:
        True if size is within limit, False otherwise
    """
    return file_size <= max_size

def format_confidence_score(score: float) -> dict:
    """
    Format confidence score with color coding
    
    Args:
        score: Confidence score between 0 and 1
    
    Returns:
        Dictionary with score and color category
    """
    if score >= 0.7:
        category = "high"
        color = "green"
    elif score >= 0.5:
        category = "medium"
        color = "yellow"
    else:
        category = "low"
        color = "red"
    
    return {
        "score": round(score, 3),
        "category": category,
        "color": color,
        "percentage": f"{round(score * 100, 1)}%"
    }

def format_error_message(error: Exception) -> dict:
    """
    Format error message for API response
    
    Args:
        error: Exception object
    
    Returns:
        Dictionary with error details
    """
    return {
        "error": type(error).__name__,
        "message": str(error),
        "success": False
    }
