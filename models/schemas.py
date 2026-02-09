"""
Pydantic models for API requests and responses
"""
from typing import List, Optional
from pydantic import BaseModel, Field

# Upload endpoint models
class UploadResponse(BaseModel):
    """Response model for document upload"""
    success: bool
    document_id: str
    filename: str
    message: str
    num_chunks: Optional[int] = None

# Ask endpoint models
class AskRequest(BaseModel):
    """Request model for asking questions"""
    document_id: str = Field(..., description="Unique document identifier")
    question: str = Field(..., min_length=1, description="Question to ask about the document")

class SourceChunk(BaseModel):
    """Model for source chunk information"""
    content: str
    similarity_score: float
    metadata: dict

class AskResponse(BaseModel):
    """Response model for question answering"""
    success: bool
    answer: str
    confidence_score: float
    confidence_category: str
    sources: List[SourceChunk]
    message: Optional[str] = None

# Extract endpoint models
class ShipmentData(BaseModel):
    """Structured shipment data model"""
    shipment_id: Optional[str] = None
    shipper: Optional[str] = None
    consignee: Optional[str] = None
    pickup_datetime: Optional[str] = None
    delivery_datetime: Optional[str] = None
    equipment_type: Optional[str] = None
    mode: Optional[str] = None
    rate: Optional[str] = None
    currency: Optional[str] = None
    weight: Optional[str] = None
    carrier_name: Optional[str] = None

class ExtractResponse(BaseModel):
    """Response model for structured extraction"""
    success: bool
    document_id: str
    shipment_data: ShipmentData
    message: Optional[str] = None

# Error response model
class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    message: str
