from typing import Dict, Union, Tuple
from fastapi import APIRouter, HTTPException, Request, Depends, Response
import re
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from services.selenium_service import SeleniumService
from utils.logger import api_logger
from utils.database import get_db, IELookup
from utils.config import settings

router = APIRouter()
thread_pool = ThreadPoolExecutor(max_workers=4)  # Limit concurrent browser sessions

def get_error_details(result: dict) -> Tuple[int, str, str]:
    """Get appropriate status code and error type based on the error."""
    error_message = result.get("error", "Unknown error")
    
    if result.get("not_found", False):
        return 404, "not_found", error_message
    if result.get("validation_error", False):
        return 422, "validation_error", error_message
    if "CAPTCHA" in error_message:
        return 417, "captcha_error", error_message
    if "webpage structure" in error_message:
        return 503, "service_unavailable", error_message
    if error_message.startswith("WebDriver"):
        return 503, "service_unavailable", error_message
    return 500, "internal_error", error_message

def validate_cnpj(cnpj: str, request_id: str = None) -> str:
    """
    Validate CNPJ format and return cleaned version.
    
    Args:
        cnpj: Raw CNPJ number
        request_id: Optional request ID for logging
        
    Returns:
        str: Cleaned CNPJ (only digits)
        
    Raises:
        HTTPException: If CNPJ format is invalid
    """
    api_logger.debug(f"Validating CNPJ format [{request_id}]: {cnpj}")
    # Remove any non-digit characters
    cleaned_cnpj = re.sub(r'\D', '', cnpj)
    
    # Validate length
    if len(cleaned_cnpj) != 14:
        api_logger.error(f"Invalid CNPJ format [{request_id}]: {cnpj}")
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "error_type": "validation_error",
                "detail": "CNPJ must contain exactly 14 digits",
                "request_id": request_id
            }
        )
    
    api_logger.debug(f"CNPJ validation successful [{request_id}]: {cleaned_cnpj}")
    return cleaned_cnpj

# Cache validity period (in days)
CACHE_VALIDITY_DAYS = 30

def is_cache_valid(last_updated: datetime) -> bool:
    """Check if cached data is still valid"""
    if not last_updated:
        return False
    return datetime.utcnow() - last_updated <= timedelta(days=CACHE_VALIDITY_DAYS)

@router.get("/api/v1/ie/{cnpj}", response_model=None)
async def get_ie(
    cnpj: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
) -> Dict[str, Union[bool, str, None]]:
    """
    Get Inscrição Estadual for given CNPJ.
    
    Args:
        cnpj: CNPJ number (can be formatted or raw)
        
    Returns:
        dict: Response containing IE number or error message
    """
    start_time = time.time()
    request_id = str(int(start_time * 1000))  # Use timestamp as request ID
    client_ip = request.client.host
    
    api_logger.info(f"Received IE lookup request [{request_id}] - CNPJ: {cnpj}, IP: {client_ip}")
    
    try:
        # Validate and clean CNPJ
        cleaned_cnpj = validate_cnpj(cnpj, request_id)
        
        # Check cache first
        cache_entry = db.query(IELookup).filter(IELookup.cnpj == cleaned_cnpj).first()
        
        # Check if we have a valid cached entry
        if cache_entry and is_cache_valid(cache_entry.last_updated) and cache_entry.ie_number is not None:
            # Update request count for valid cache hits
            cache_entry.request_count += 1
            db.commit()
            
            api_logger.info(
                f"Valid cache hit for CNPJ {cleaned_cnpj} [{request_id}] - "
                f"IE: {cache_entry.ie_number}, Times requested: {cache_entry.request_count}"
            )
            
            response.status_code = 200  # OK
            return {
                "status": "success",
                "ie_number": cache_entry.ie_number,
                "request_id": request_id,
                "processing_time": "0.00s",
                "cached": True
            }
        
        # If not in cache, cache invalid, or cached IE is null, fetch from service
        if cache_entry and cache_entry.ie_number is None:
            api_logger.info(f"Cached IE is null for {cleaned_cnpj}, attempting fresh lookup")
        selenium_service = SeleniumService()
        result = None
        retries = 0
        max_retries = 3
        
        # Function to fetch from CADESP
        async def fetch_from_cadesp():
            return await request.app.state.loop.run_in_executor(
                thread_pool,
                selenium_service.get_ie_number,
                cleaned_cnpj
            )

        # Initial attempt
        while retries <= max_retries:
            result = await fetch_from_cadesp()
            
            # If we got a success with valid IE number, break
            if result["success"] and result.get("ie_number") is not None:
                api_logger.debug(f"Got valid IE on attempt {retries + 1}")
                break
            
            # If we got a success but null IE, retry
            if result["success"] and result.get("ie_number") is None:
                retries += 1
                if retries <= max_retries:
                    api_logger.warning(f"Got null IE, retrying (attempt {retries}/{max_retries})")
                    time.sleep(2)  # Brief delay between retries
                    continue
            
            # If we got an error, break (don't retry)
            break

        # Always update cache with latest attempt, even if null
        elapsed_time = time.time() - start_time
        success = result["success"]

        # Update cache with latest attempt
        if cache_entry:
            # Update existing entry
            cache_entry.ie_number = result.get("ie_number")
            cache_entry.last_updated = datetime.utcnow()
            cache_entry.request_count += 1
            cache_entry.last_success = success
            cache_entry.processing_time = elapsed_time
        else:
            # Create new entry
            cache_entry = IELookup(
                cnpj=cleaned_cnpj,
                ie_number=result.get("ie_number"),
                last_success=success,
                processing_time=elapsed_time
            )
            db.add(cache_entry)
        
        db.commit()
        
        # Handle errors and not found cases
        if not success:
            error_message = result.get("error", "Unknown error")
            status_code, error_type, error_detail = get_error_details(result)
            
            api_logger.warning(
                f"IE lookup failed [{request_id}] - CNPJ: {cnpj}, "
                f"Error Type: {error_type}, Error: {error_detail}, Time: {elapsed_time:.2f}s"
            )
            
            response.status_code = status_code
            return {
                "status": "error",
                "error_type": error_type,
                "detail": error_detail,
                "request_id": request_id,
                "processing_time": f"{elapsed_time:.2f}s"
            }
            
        # Log successful lookup
        ie_number = result.get("ie_number")
        api_logger.info(
            f"IE lookup successful [{request_id}] - CNPJ: {cnpj}, "
            f"IE: {ie_number}, Time: {elapsed_time:.2f}s"
        )
        
        response.status_code = 200
        return {
            "status": "success",
            "ie_number": ie_number,
            "request_id": request_id,
            "processing_time": f"{elapsed_time:.2f}s",
            "cached": False
        }
        
    except HTTPException as e:
        raise
    except Exception as e:
        api_logger.error(
            f"Unexpected error in IE lookup [{request_id}] - CNPJ: {cnpj}, "
            f"Error: {str(e)}", exc_info=True
        )
        return {
            "status": "error",
            "error_type": "internal_error",
            "detail": str(e),
            "request_id": request_id,
            "processing_time": f"{time.time() - start_time:.2f}s"
        }
