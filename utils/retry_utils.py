"""
Retry utilities for API calls with exponential backoff
"""
import logging
from typing import Callable
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)

# Configure logging
logger = logging.getLogger(__name__)

# Custom exception classes
class RateLimitError(Exception):
    """Raised when API rate limit is hit"""
    pass

class TokenLimitError(Exception):
    """Raised when token limit is exceeded"""
    pass

class ServiceUnavailableError(Exception):
    """Raised when service is temporarily unavailable"""
    pass

def is_retriable_error(exception: Exception) -> bool:
    """Check if an exception is retriable"""
    error_msg = str(exception).lower()
    
    # Check for rate limit errors
    if "rate limit" in error_msg or "429" in error_msg:
        return True
    
    # Check for token limit errors
    if "token limit" in error_msg or "tokens" in error_msg:
        return True
    
    # Check for service unavailable
    if "503" in error_msg or "service unavailable" in error_msg:
        return True
    
    # Check for timeout errors
    if "timeout" in error_msg:
        return True
    
    return False

def retry_on_api_error(func: Callable) -> Callable:
    """
    Decorator for retrying API calls with exponential backoff
    
    Retry strategy:
    - Max 3 attempts
    - Exponential backoff: 1s, 2s, 4s, 8s
    - Retries on rate limit, token limit, and service errors
    """
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((
            RateLimitError,
            TokenLimitError,
            ServiceUnavailableError,
            ConnectionError,
            TimeoutError
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        reraise=True
    )
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Convert generic exceptions to specific ones if they match retry conditions
            if is_retriable_error(e):
                error_msg = str(e).lower()
                if "rate limit" in error_msg or "429" in error_msg:
                    raise RateLimitError(str(e)) from e
                elif "token limit" in error_msg or "tokens" in error_msg:
                    raise TokenLimitError(str(e)) from e
                elif "503" in error_msg or "service unavailable" in error_msg:
                    raise ServiceUnavailableError(str(e)) from e
            # Re-raise the original exception if not retriable
            raise
    
    return wrapper
