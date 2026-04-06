"""
Router untuk history scan endpoints.
Menyediakan CRUD operations untuk scan history.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
from typing import Optional, List
from database import get_db, ScanHistory, CleanupLog, cleanup_old_records

router = APIRouter()

# ===========================================
# GET /history - List semua scan dengan pagination & filter
# ===========================================
@router.get("/history", summary="Get scan history with filtering")
async def get_scan_history(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    verdict: Optional[str] = Query(None, description="Filter by verdict (safe/suspicious/phishing)"),
    search: Optional[str] = Query(None, description="Search by filename"),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO format: 2026-04-01)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO format: 2026-04-02)"),
    db: Session = Depends(get_db)
):
    """
    Get scan history with filtering and pagination.
    
    **Filters:**
    - verdict: Filter by scan result (safe/suspicious/phishing)
    - search: Search by filename (case-insensitive)
    - date_from: Filter scans from this date
    - date_to: Filter scans until this date
    
    **Pagination:**
    - page: Page number (starts from 1)
    - limit: Items per page (max 100)
    """
    # Build query
    query = db.query(ScanHistory)
    
    # Filter by verdict
    if verdict:
        if verdict not in ["safe", "suspicious", "phishing"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verdict. Must be: safe, suspicious, or phishing"
            )
        query = query.filter(ScanHistory.verdict == verdict)
    
    # Search by filename (case-insensitive)
    if search:
        query = query.filter(ScanHistory.filename.ilike(f"%{search}%"))
    
    # Filter by date range
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from)
            query = query.filter(ScanHistory.scanned_at >= date_from_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_from format. Use ISO format: YYYY-MM-DD"
            )
    
    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to)
            # Include the entire end date
            date_to_dt = date_to_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(ScanHistory.scanned_at <= date_to_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_to format. Use ISO format: YYYY-MM-DD"
            )
    
    # Count total for pagination
    total = query.count()
    
    # Apply pagination and sort by newest first
    offset = (page - 1) * limit
    results = query.order_by(desc(ScanHistory.scanned_at)).offset(offset).limit(limit).all()
    
    return {
        "items": [item.to_dict() for item in results],
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 0
    }

# ===========================================
# GET /history/{scan_id} - Get detail scan by ID
# ===========================================
@router.get("/history/{scan_id}", summary="Get scan detail by ID")
async def get_scan_detail(scan_id: int, db: Session = Depends(get_db)):
    """
    Get detailed scan result by ID.
    Includes full result_data for technical analysis.
    """
    result = db.query(ScanHistory).filter(ScanHistory.id == scan_id).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan record {scan_id} not found"
        )
    
    return {
        **result.to_dict(),
        "result_data": result.result_data  # Full technical details
    }

# ===========================================
# DELETE /history/{scan_id} - Delete individual record
# ===========================================
@router.delete("/history/{scan_id}", summary="Delete scan record")
async def delete_scan_record(scan_id: int, db: Session = Depends(get_db)):
    """
    Delete individual scan record.
    Useful for removing sensitive scans or cleaning up test data.
    """
    result = db.query(ScanHistory).filter(ScanHistory.id == scan_id).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan record {scan_id} not found"
        )
    
    db.delete(result)
    db.commit()
    
    return {
        "status": "success",
        "message": f"Record {scan_id} deleted successfully"
    }

# ===========================================
# POST /history/cleanup - Manual trigger cleanup
# ===========================================
@router.post("/history/cleanup", summary="Trigger cleanup of old records")
async def trigger_cleanup(
    retention_days: int = Query(30, ge=1, le=365, description="Days to retain records"),
    db: Session = Depends(get_db)
):
    """
    Manually trigger cleanup of old records.
    
    **Note:** Auto-cleanup runs daily, but this endpoint allows manual trigger.
    """
    result = cleanup_old_records(db, retention_days)
    
    if result["status"] == "success":
        return {
            "status": "success",
            "message": f"Deleted {result['deleted']} records older than {retention_days} days"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Cleanup failed")
        )

# ===========================================
# GET /dashboard/stats - Dashboard statistics
# ===========================================
@router.get("/dashboard/stats", summary="Get dashboard statistics")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get dashboard statistics for overview page.
    Includes total scans, breakdown by verdict, and recent activity.
    """
    # Total scans
    total = db.query(func.count(ScanHistory.id)).scalar() or 0
    
    # Count by verdict
    safe = db.query(func.count(ScanHistory.id)).filter(
        ScanHistory.verdict == "safe"
    ).scalar() or 0
    
    suspicious = db.query(func.count(ScanHistory.id)).filter(
        ScanHistory.verdict == "suspicious"
    ).scalar() or 0
    
    phishing = db.query(func.count(ScanHistory.id)).filter(
        ScanHistory.verdict == "phishing"
    ).scalar() or 0
    
    # Recent scans (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent = db.query(func.count(ScanHistory.id)).filter(
        ScanHistory.scanned_at >= yesterday
    ).scalar() or 0
    
    # Recent scans (last 7 days)
    last_week = datetime.utcnow() - timedelta(days=7)
    week_scans = db.query(func.count(ScanHistory.id)).filter(
        ScanHistory.scanned_at >= last_week
    ).scalar() or 0
    
    # Top threatened domains (optional)
    # threatened_domains = db.query(
    #     ScanHistory.from_domain, 
    #     func.count(ScanHistory.id)
    # ).filter(
    #     ScanHistory.verdict == "phishing"
    # ).group_by(ScanHistory.from_domain).order_by(
    #     func.count(ScanHistory.id).desc()
    # ).limit(5).all()
    
    return {
        "total_scans": total,
        "safe": safe,
        "suspicious": suspicious,
        "phishing": phishing,
        "recent_24h": recent,
        "recent_7d": week_scans,
        "last_updated": datetime.utcnow().isoformat()
    }

# ===========================================
# GET /history/cleanup/logs - View cleanup logs
# ===========================================
@router.get("/history/cleanup/logs", summary="View cleanup job logs")
async def get_cleanup_logs(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    View recent cleanup job logs.
    Useful for monitoring auto-cleanup activity.
    """
    logs = db.query(CleanupLog).order_by(
        desc(CleanupLog.executed_at)
    ).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "executed_at": log.executed_at.isoformat() if log.executed_at else None,
                "records_deleted": log.records_deleted,
                "status": log.status,
                "error_message": log.error_message
            }
            for log in logs
        ]
    }