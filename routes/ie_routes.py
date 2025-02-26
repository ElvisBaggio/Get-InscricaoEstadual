from typing import Dict, Union
from fastapi import APIRouter, HTTPException, Request
import re
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from services.selenium_service import SeleniumService
from utils.logger import api_logger

router = APIRouter()
thread_pool = ThreadPoolExecutor(max_workers=4)  # Limit concurrent browser sessions

def validate_cnpj(cnpj: str, request_id: str = None) -> str:
    """
    Validate CNPJ format and return cleaned version.
    
    Args:
        cnpj: Raw CNPJ number
        
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
            detail="CNPJ must contain exactly 14 digits"
        )
    
    api_logger.debug(f"CNPJ validation successful [{request_id}]: {cleaned_cnpj}")
    return cleaned_cnpj

@router.get("/api/v1/ie/{cnpj}", response_model=None)
async def get_ie(cnpj: str, request: Request) -> Dict[str, Union[bool, str, None]]:
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
        
        # Initialize service and get IE in a thread pool
        selenium_service = SeleniumService()
        result = await request.app.state.loop.run_in_executor(
            thread_pool,
            selenium_service.get_ie_number,
            cleaned_cnpj
        )
        
        elapsed_time = time.time() - start_time
        
        # Handle errors and not found cases
        if not result["success"] or result.get("ie_number") is None:
            error_message = result.get("error", "Unknown error")
            # Use 404 status for CNPJs not found in database, 500 for other errors
            status_code = 404 if result.get("not_found", False) else 500
            
            api_logger.error(
                f"IE lookup failed [{request_id}] - CNPJ: {cnpj}, "
                f"Error: {error_message}, Time: {elapsed_time:.2f}s"
            )
            raise HTTPException(
                status_code=status_code,
                detail=error_message
            )
            
        # Log successful lookup
        ie_number = result.get("ie_number")
        api_logger.info(
            f"IE lookup successful [{request_id}] - CNPJ: {cnpj}, "
            f"IE: {ie_number}, Time: {elapsed_time:.2f}s"
        )
        
        return {"ie_number": ie_number, "request_id": request_id, "processing_time": f"{elapsed_time:.2f}s"}
        
    except HTTPException as e:
        raise
    except Exception as e:
        api_logger.error(
            f"Unexpected error in IE lookup [{request_id}] - CNPJ: {cnpj}, "
            f"Error: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
