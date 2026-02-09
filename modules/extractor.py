"""
Structured data extraction from logistics documents
"""
import logging
import json
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma

from config.settings import settings
from utils.retry_utils import retry_on_api_error
from models.schemas import ShipmentData

logger = logging.getLogger(__name__)

class StructuredExtractor:
    """Extract structured shipment data from documents using LLM"""
    
    def __init__(self):
        """Initialize extractor with ChatGroq LLM"""
        self.llm = self._initialize_llm()
    
    @retry_on_api_error
    def _initialize_llm(self) -> ChatGroq:
        """
        Initialize ChatGroq LLM with retry mechanism
        
        Returns:
            ChatGroq instance
        """
        try:
            llm = ChatGroq(
                model=settings.LLM_MODEL,
                groq_api_key=settings.GROQ_API_KEY,
                temperature=0.0
            )
            logger.info("ChatGroq LLM initialized for extraction")
            return llm
        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}")
            raise
    
    def _create_extraction_prompt(self, document_text: str) -> str:
        """
        Create prompt for structured extraction
        
        Args:
            document_text: Full text or relevant portions of document
            
        Returns:
            Formatted prompt string
        """
        template = """You are an expert at extracting structured data from logistics documents.

Your task is to extract the following shipment information from the provided document text.
Return ONLY a JSON object with these exact fields. Use null for any field not found in the document.

Required fields:
- shipment_id: Shipment or order ID
- shipper: Name or company shipping the goods
- consignee: Name or company receiving the goods
- pickup_datetime: Scheduled pickup date and time
- delivery_datetime: Scheduled or expected delivery date and time
- equipment_type: Type of equipment (e.g., "53' Dry Van", "Flatbed", "Reefer")
- mode: Transportation mode (e.g., "LTL", "FTL", "Parcel")
- rate: Transportation rate or cost
- currency: Currency for the rate (e.g., "USD", "CAD")
- weight: Total weight of shipment
- carrier_name: Name of the carrier company

IMPORTANT RULES:
1. Extract information EXACTLY as it appears in the document
2. Return valid JSON format only, no additional text
3. Use null for missing fields, not empty strings
4. Preserve original formatting for dates, numbers, and names
5. Do not make assumptions or infer missing data

Document Text:
{document_text}

JSON Output:"""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["document_text"]
        )
        
        return prompt.format(document_text=document_text)
    
    def _get_document_context(self, vector_store: Chroma, max_chunks: int = 5) -> str:
        """
        Get full document context from vector store
        
        Args:
            vector_store: ChromaDB vector store
            max_chunks: Maximum number of chunks to retrieve
            
        Returns:
            Combined text from document chunks
        """
        try:
            # Get all documents from the collection
            # Use a generic query to get top chunks
            results = vector_store.similarity_search(
                "shipment carrier consignee shipper pickup delivery rate",
                k=max_chunks
            )
            
            # Combine chunks
            combined_text = "\n\n".join([doc.page_content for doc in results])
            
            return combined_text
            
        except Exception as e:
            logger.error(f"Error getting document context: {str(e)}")
            raise
    
    @retry_on_api_error
    def extract_shipment_data(self, vector_store: Chroma, document_id: str) -> ShipmentData:
        """
        Extract structured shipment data from document
        
        Args:
            vector_store: ChromaDB vector store for the document
            document_id: Document identifier
            
        Returns:
            ShipmentData object with extracted fields
        """
        try:
            # Get document context
            document_text = self._get_document_context(vector_store)
            
            logger.info(f"Extracting structured data from document {document_id}")
            
            # Create extraction prompt
            prompt = self._create_extraction_prompt(document_text)
            
            # Get LLM response
            response = self.llm.invoke(prompt)
            result_text = response.content.strip()
            
            # Parse JSON response
            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            result_text = result_text.strip()
            
            # Parse JSON
            try:
                extracted_data = json.loads(result_text)
            except json.JSONDecodeError as je:
                logger.error(f"Failed to parse JSON: {result_text}")
                # Return empty ShipmentData if parsing fails
                extracted_data = {}
            
            # Create ShipmentData object
            shipment_data = ShipmentData(**extracted_data)
            
            logger.info(f"Successfully extracted shipment data from document {document_id}")
            return shipment_data
            
        except Exception as e:
            logger.error(f"Error extracting shipment data: {str(e)}")
            # Return empty ShipmentData on error
            return ShipmentData()
