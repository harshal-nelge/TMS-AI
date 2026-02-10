"""
RAG engine for question answering with guardrails and confidence scoring
"""
import logging
from typing import List, Dict, Any, Tuple
from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate

from config.settings import settings
from utils.retry_utils import retry_on_api_error

logger = logging.getLogger(__name__)

class RAGEngine:
    """RAG-based question answering with confidence scoring and guardrails"""
    
    def __init__(self):
        """Initialize RAG engine with ChatGroq LLM"""
        self.llm = self._initialize_llm()
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
    
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
                temperature=settings.LLM_TEMPERATURE
            )
            logger.info(f"ChatGroq LLM initialized with model: {settings.LLM_MODEL}")
            return llm
        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}")
            raise
    
    def calculate_confidence_score(
        self, 
        retrieval_scores: List[float],
        answer: str,
        sources: List[Document]
    ) -> Tuple[float, str]:
        """
        Calculate confidence score based on retrieval similarity and source agreement
        
        Args:
            retrieval_scores: List of similarity scores from retrieval
            answer: Generated answer text
            sources: Retrieved source documents
            
        Returns:
            Tuple of (confidence_score, category)
        """
        # Calculate average retrieval similarity score
        # Note: ChromaDB returns lower scores for better matches (distance metric)
        # Convert to similarity: 1 - normalized_distance
        avg_similarity = 1 - (sum(retrieval_scores) / len(retrieval_scores))
        
        # Check source agreement - do multiple sources contain similar information?
        source_agreement = 1.0 if len(sources) >= 2 else 0.7
        
        # Weighted confidence score
        confidence = (
            settings.SIMILARITY_WEIGHT * avg_similarity +
            settings.AGREEMENT_WEIGHT * source_agreement
        )
        
        # Determine category
        if confidence >= 0.7:
            category = "high"
        elif confidence >= 0.5:
            category = "medium"
        else:
            category = "low"
        
        logger.info(
            f"Confidence: {confidence:.3f} (similarity: {avg_similarity:.3f}, "
            f"agreement: {source_agreement:.3f})"
        )
        
        return confidence, category
    
    def apply_guardrails(self, confidence: float, retrieval_scores: List[float]) -> bool:
        """
        Apply guardrails to determine if answer should be returned
        
        Args:
            confidence: Overall confidence score
            retrieval_scores: List of retrieval similarity scores
            
        Returns:
            True if answer passes guardrails, False otherwise
        """
        # Check if average retrieval score passes threshold
        avg_retrieval = 1 - (sum(retrieval_scores) / len(retrieval_scores))
        
        if avg_retrieval < self.similarity_threshold:
            logger.warning(
                f"Guardrail triggered: Retrieval score {avg_retrieval:.3f} "
                f"below threshold {self.similarity_threshold}"
            )
            return False
        
        if confidence < self.similarity_threshold:
            logger.warning(
                f"Guardrail triggered: Confidence {confidence:.3f} "
                f"below threshold {self.similarity_threshold}"
            )
            return False
        
        return True
    
    def _create_prompt(self, question: str, context: str) -> str:
        """
        Create prompt for LLM
        
        Args:
            question: User's question
            context: Retrieved context from documents
            
        Returns:
            Formatted prompt string
        """
        template = """You are a helpful AI assistant for a Transportation Management System (TMS). 
Your task is to answer questions about logistics documents accurately and concisely.

IMPORTANT RULES:
1. Answer ONLY based on the provided context below
2. If the context doesn't contain the information, say "The information is not found in the document"
3. Be specific and cite relevant details from the context
4. Keep answers concise and factual
5. Do not make up or infer information not present in the context

Context from document:
{context}

Question: {question}

Answer:"""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        return prompt.format(context=context, question=question)
    
    @retry_on_api_error
    def generate_answer(
        self,
        question: str,
        retrieved_docs: List[Tuple[Document, float]]
    ) -> Dict[str, Any]:
        """
        Generate answer using RAG with retry mechanism
        
        Args:
            question: User's question
            retrieved_docs: List of (Document, score) tuples from retrieval
            
        Returns:
            Dictionary containing answer, sources, and confidence information
        """
        try:
            # Extract documents and scores
            documents = [doc for doc, score in retrieved_docs]
            scores = [score for doc, score in retrieved_docs]
            
            # Create context from retrieved documents
            context = "\n\n---\n\n".join([
                f"[Source {i+1}]:\n{doc.page_content}"
                for i, doc in enumerate(documents)
            ])
            
            # Generate answer using LLM
            prompt = self._create_prompt(question, context)
            response = self.llm.invoke(prompt)
            answer = response.content
            
            # Calculate confidence score
            confidence, category = self.calculate_confidence_score(
                scores, answer, documents
            )
            
            # Apply guardrails
            passes_guardrails = self.apply_guardrails(confidence, scores)
            
            if not passes_guardrails:
                answer = "I cannot provide a confident answer based on the available context. The information might not be present in the document, or the retrieved content has low relevance to your question."
                category = "low"
            
            # Format sources
            sources = [
                {
                    "content": doc.page_content,
                    "similarity_score": round(1 - score, 3),
                    "metadata": doc.metadata
                }
                for doc, score in retrieved_docs
            ]
            
            result = {
                "answer": answer,
                "confidence_score": round(confidence, 3),
                "confidence_category": category,
                "sources": sources,
                "passes_guardrails": passes_guardrails
            }
            
            logger.info(f"Generated answer with confidence: {confidence:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise
    
    def ask_question(
        self,
        vector_store: Chroma,
        question: str
    ) -> Dict[str, Any]:
        """
        Complete RAG pipeline for question answering
        
        Args:
            vector_store: ChromaDB vector store instance
            question: User's question
            
        Returns:
            Dictionary with answer and metadata
        """
        # Import here to avoid circular dependency
        from modules.vector_store import VectorStoreManager
        
        vsm = VectorStoreManager()
        
        # Retrieve relevant chunks
        retrieved_docs = vsm.similarity_search(
            vector_store, 
            question,
            k=settings.TOP_K_RETRIEVAL
        )
        
        if not retrieved_docs:
            return {
                "answer": "No relevant information found in the document.",
                "confidence_score": 0.0,
                "confidence_category": "low",
                "sources": [],
                "passes_guardrails": False
            }
        
        # Generate answer with confidence scoring
        result = self.generate_answer(question, retrieved_docs)
        
        return result
