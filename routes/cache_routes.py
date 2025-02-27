from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, List

from utils.database import get_db, IELookup
from utils.logger import api_logger

router = APIRouter()

@router.delete("/api/v1/cache/{cnpj}", response_model=Dict[str, str])
async def clear_cache_entry(cnpj: str, db: Session = Depends(get_db)):
    """Clear a specific CNPJ from cache"""
    cache_entry = db.query(IELookup).filter(IELookup.cnpj == cnpj).first()
    if not cache_entry:
        raise HTTPException(status_code=404, detail="CNPJ not found in cache")
    
    db.delete(cache_entry)
    db.commit()
    
    api_logger.info(f"Cleared cache entry for CNPJ: {cnpj}")
    return {"message": f"Cache cleared for CNPJ: {cnpj}"}

@router.delete("/api/v1/cache", response_model=Dict[str, str])
async def clear_all_cache(db: Session = Depends(get_db)):
    """Clear all entries from cache"""
    db.query(IELookup).delete()
    db.commit()
    
    api_logger.info("Cleared all cache entries")
    return {"message": "All cache entries cleared"}

@router.get("/api/v1/cache/stats", response_model=Dict[str, object])
async def get_cache_stats(db: Session = Depends(get_db)):
    """Get cache statistics"""
    total_entries = db.query(IELookup).count()
    most_requested = db.query(IELookup).order_by(IELookup.request_count.desc()).limit(5).all()
    latest_updates = db.query(IELookup).order_by(IELookup.last_updated.desc()).limit(5).all()
    
    return {
        "total_entries": total_entries,
        "most_requested": [
            {
                "cnpj": entry.cnpj,
                "request_count": entry.request_count,
                "last_updated": entry.last_updated.isoformat() if entry.last_updated else None
            }
            for entry in most_requested
        ],
        "latest_updates": [
            {
                "cnpj": entry.cnpj,
                "last_updated": entry.last_updated.isoformat() if entry.last_updated else None,
                "success": entry.last_success
            }
            for entry in latest_updates
        ]
    }
