# This is your main router, moved from app/routes.py
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi import status as http_status
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
from app.database import get_db
from app.services import QueryHandlerService
from app.schemas import QueueListResponse, CaseDetailsResponse, CallOutcomeResponse, ErrorResponse

router = APIRouter(
    prefix="/collections",
    tags=["collections"]
)

@router.get(
    "/health",
    summary="Health Check",
    description="Check API health status"
)
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

@router.get(
    "/queue",
    response_model=QueueListResponse,
    summary="Get Queue",
    description="Retrieve the current call queue"
)
def get_queue(
    db: Session = Depends(get_db)
):
    """
    Get the current call queue.
    """
    try:
        service = QueryHandlerService(db)
        response = service.get_collection_queue()
        return response
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving queue: {str(e)}"
        )

@router.get(
    "/case/{case_id}/details",
    response_model=CaseDetailsResponse,
    summary="Get Case Details",
    description="Retrieve detailed information about a specific case"
)
def get_case_details(
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific case including:
    - Customer information
    - Invoice details
    - Outstanding balance and age calculations
    - Call history
    - All actions taken on the case
    Args:
        case_id: Unique case identifier
    """
    try:
        service = QueryHandlerService(db)
        response = service.get_case_details(case_id)
        return response
    except ValueError as ve:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving case details: {str(e)}"
        )

@router.get(
    "/call/{call_id}",
    response_model=CallOutcomeResponse,
    summary="Get Call Details",
    description="Retrieve detailed information about a specific call"
)
def get_call_details(
    call_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific call.
    Args:
        call_id: Unique call identifier
    """
    try:
        service = QueryHandlerService(db)
        response = service.get_call_details(call_id)
        return response
    except ValueError as ve:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving call details: {str(e)}"
        )
