from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CustomerMasterData, InvoiceBalanceTable, CallQueue, ARTransaction, CustomerMaster, CollectionQueue, CallOutcome
from app.schemas import (
    CallNote, InvoiceItem, CallFailed, CallData, CollectionQueueCreate, CollectionQueueSlimOut
)
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.exc import IntegrityError
from psycopg2.extras import DateTimeRange
import uuid
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal
from typing import Optional, List, Any, Dict


router = APIRouter()

# New endpoint to list all call_id values from CallOutcome
@router.get("/collections/call_ids", summary="Get all call IDs", tags=["Collections"])
def get_all_call_ids(db: Session = Depends(get_db)):
    """
    Returns a list of all available call_id values in the CallOutcome table.
    Use these IDs to query /collections/call/{call_id} for details.
    """
    call_ids = db.query(CallOutcome.call_id).all()
    return {"call_ids": [c[0] for c in call_ids]}

def now_utc() -> datetime:
    # Return tz-naive UTC (consistent with many DB configs)
    return datetime.now(dt_timezone.utc).replace(tzinfo=None)

def generate_uniqid() -> str:
    return uuid.uuid4().hex

def generate_case_id(tenant_id: str, customer_id: uuid.UUID, uniqid: str) -> str:
    return f"{tenant_id}-{str(customer_id)}-{uniqid}"

def normalize_notes(notes: Optional[List[CallNote]]) -> Optional[List[dict]]:
    if not notes:
        return None

    def normalize(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: normalize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [normalize(v) for v in obj]
        return obj

    out = []
    for n in notes:
        data = n.model_dump()
        if not data.get("created_at"):
            data["created_at"] = now_utc()
        out.append(normalize(data))
    return out

def invoice_items_to_json(items: Optional[List[InvoiceItem]]) -> Optional[List[dict]]:
    if not items:
        return None

    def normalize(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: normalize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [normalize(v) for v in obj]
        return obj

    raw = [i.model_dump(by_alias=False) for i in items]
    return normalize(raw)

def validate_invoices_belong_to_customer(
    db: Session, customer_id: uuid.UUID, items: Optional[List[InvoiceItem]]
) -> None:
    """Strict validation: ensure provided invoice document_numbers exist for the given customer."""
    if not items:
        return
    doc_nums = [i.document_number for i in items if i.document_number]
    if not doc_nums:
        return
    found = (
        db.query(ARTransaction.document_number)
        .filter(ARTransaction.customer_id == customer_id, ARTransaction.document_number.in_(doc_nums))
        .all()
    )
    found_set = {r[0] for r in found}
    missing = [d for d in doc_nums if d not in found_set]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown invoice document_number(s) for this customer: {missing}",
        )

def to_tsrange_tuple(window):
    if not window:
        return None
    start, end = window
    # enforce naive datetimes for tsrange
    if start.tzinfo is not None or end.tzinfo is not None:
        raise HTTPException(400, "calling_window must be naive (no timezone).")
    if end <= start:
        raise HTTPException(400, "calling_window end must be greater than start.")
    return DateTimeRange(start, end, bounds='[]')

# ------------------------------------------------------------------------------
# Endpoint: /call-handle/
# ------------------------------------------------------------------------------
@router.get("/customers/")
def list_customers(db: Session = Depends(get_db)):
    return db.query(CustomerMaster).all()

@router.get("/invoices/")
def list_invoices(db: Session = Depends(get_db)):
    return db.query(ARTransaction).all()


# @router.get("/totalcollections/")
# def list_invoices(db: Session = Depends(get_db)):
#     return db.query(CollectionQueue).all()



@router.post("/call-handle/", response_model=CollectionQueueSlimOut, status_code=status.HTTP_201_CREATED)
def create_collection_case(payload: CollectionQueueCreate, db: Session = Depends(get_db)):
    customer = (
        db.query(CustomerMaster)
        .filter(CustomerMaster.customer_id == payload.customer_id)
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    tenant_id = customer.tenant_id
    customer_name = customer.customer_name
    contact_name = customer.contact_name
    billing_address = customer.billing_address
    phone_number = customer.phone_number
    email_address = customer.email_address
    preferred_language = customer.preferred_language

    uniqid = generate_uniqid()
    case_id = generate_case_id(tenant_id, payload.customer_id, uniqid)

    validate_invoices_belong_to_customer(db, payload.customer_id, payload.invoice_numbers)

    exists = (
        db.query(CollectionQueue)
        .filter(
            CollectionQueue.tenant_id == tenant_id,
            CollectionQueue.customer_id == payload.customer_id,
            CollectionQueue.uniqid == uniqid,
        )
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=409,
            detail="A case for the same tenant_id + customer_id + uniqid already exists."
        )

    invoice_json = invoice_items_to_json(payload.invoice_numbers)
    notes_json = normalize_notes(payload.call_notes)

    multiple_invoice = payload.multiple_invoice
    if multiple_invoice is None and invoice_json is not None:
        multiple_invoice = len(invoice_json) > 1

    # if payload.activity_status is False or payload.activity_status is None:
    #     if not payload.activity_empty_reason or payload.activity_empty_reason.strip().lower() in ["", "string", "null", "none"]:
    #         raise HTTPException(
    #             status_code=400,
    #             detail="activity_empty_reason is required when activity_status is false or empty."
    #         )

    # if payload.dnc_status is True:
    #     if not payload.dnc_reason_yes or payload.dnc_reason_yes.strip().lower() in ["", "string", "null", "none"]:
    #         raise HTTPException(
    #             status_code=400,
    #             detail="dnc_reason_yes is required when dnc_status is true."
    #         )

    if payload.calling_window and not payload.time_zone:
        raise HTTPException(
            status_code=400,
            detail="time_zone is required when calling_window is provided."
        )

    calling_window_range = to_tsrange_tuple(payload.calling_window)

    rec = CollectionQueue(
        case_id=case_id,
        tenant_id=tenant_id,
        customer_id=payload.customer_id,
        uniqid=uniqid,
        customer_name=customer_name,
        contact_name=contact_name,
        preferred_language=preferred_language,
        billing_address=billing_address,
        phone_number=phone_number,
        email_address=email_address,
        invoice_numbers=invoice_json,
        multiple_invoice=multiple_invoice,
        aging_bucket=payload.aging_bucket,
        priority=payload.priority,
        due_at=payload.due_at,
        call_notes=notes_json,
        call_type=payload.call_type,
        activity_status=payload.activity_status,
        # activity_empty_reason=payload.activity_empty_reason,
        dnc_status=payload.dnc_status,
        # dnc_reason_yes=payload.dnc_reason_yes,
        record_consent=payload.record_consent,
        calling_window=calling_window_range,  # (start, end) as local naive datetimes
        time_zone=payload.time_zone,
        call_data=payload.call_data,
        call_failed=payload.call_failed.model_dump() if payload.call_failed else None
    )

    db.add(rec)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A case for the same tenant_id + customer_id + uniqid already exists."
        )

    db.refresh(rec)

    # Slim response
    return {
        "case_id": rec.case_id,
        "customer_id": rec.customer_id,
        "user_name": rec.customer_name,
        "billing_address": rec.billing_address,
        "contact_name": rec.contact_name,
        "user_phone": rec.phone_number,
        "user_email": rec.email_address,
        "preferred_language": rec.preferred_language,
        "preferred_contact_hours": [payload.calling_window[0], payload.calling_window[1]] if payload.calling_window else None,
        "call_type": rec.call_type,
        "time_zone": rec.time_zone,
        "attempt_number": rec.call_data.get("attempt_number") if rec.call_data else None,
        "multiple_invoice": rec.multiple_invoice,
        "call_data": rec.call_data,
        "call_failed": rec.call_failed,
    }



@router.get("/call-workflow/{case_id}")
def get_call_workflow(case_id: str, db: Session = Depends(get_db)):
    """
    Fetch a single call workflow by case_id.
    Returns customer_info, invoice_info, call_handler_info, attempt_number.
    """

    case = db.query(CollectionQueue).filter(
        CollectionQueue.case_id == case_id
    ).first()

    if not case:
        raise HTTPException(404, "Case ID not found")

    customer = db.query(CustomerMaster).filter(
        CustomerMaster.customer_id == case.customer_id
    ).first()

    if not customer:
        raise HTTPException(404, "Customer record missing for this case")

    customer_info = {
        "customer_id": str(customer.customer_id),
        "customer_name": customer.customer_name,
        "billing_address": customer.billing_address,
        "contact_name": customer.contact_name,
        "phone_number": customer.phone_number,
        "email_address": customer.email_address,
        "preferred_language": customer.preferred_language,
        "time_zone": customer.time_zone
    }

    # ----------------------------
    # 2. Invoice Info
    # ----------------------------
    invoices = db.query(ARTransaction).filter(
        ARTransaction.customer_id == case.customer_id
    ).all()

    invoice_info = []
    for i in invoices:
        invoice_info.append({
            "document_number": i.document_number,
            "outstanding_balance": float(i.outstanding_balance or 0),
            "due_date": i.due_date.isoformat() if i.due_date else None,
            "days_past_due": i.days_past_due,
            "open_ptp": i.open_ptp,
            "open_dispute": i.open_dispute,
        })

    # ----------------------------
    # 3. Call Handler Info
    # ----------------------------
    call_handler = case.call_data or {}
    attempt_number = call_handler.get("attempt_number", 0)
    fail_status = case.call_failed

    

    return {
        "case_id": case.case_id,
        "attempt_number": attempt_number,
        "customer_info": customer_info,
        "invoice_info": invoice_info,
        "call_handler": call_handler,
        "call_failed": fail_status
    }




@router.post("/call-workflow/")
def call_workflow(
    payload: dict = Body(default={}),
    db: Session = Depends(get_db)
):
    """
    - If no payload -> return ALL workflow cases
    - If case_id provided -> return/modify EXACT case
    - If call_failed.status = failed -> increment attempt_number for that case
    """

    case_id = payload.get("case_id")
    # call_failed = payload.get("call_failed")

    # --------------------------------------------------
    # CASE 1 → NO PAYLOAD → RETURN ALL CASES
    # --------------------------------------------------
    if not case_id:
        all_cases = db.query(CollectionQueue).all()

        results = []
        for case in all_cases:
            results.append(build_case_workflow_json(
                db=db,
                case=case
                
            ))

        return {
            "total_cases": len(results),
            "workflows": results
        }

    # --------------------------------------------------
    # CASE 2 → SPECIFIC CASE PROVIDED
    # --------------------------------------------------
    case = db.query(CollectionQueue).filter(
        CollectionQueue.case_id == case_id
    ).first()

    if not case:
        raise HTTPException(404, "Case ID not found")

    return build_case_workflow_json(
        db=db,
        case=case, payload=payload
    )


# Updated docstring for /collections/call/{call_id} endpoint
from fastapi import Path

@router.get(
    "/collections/call/{call_id}",
    summary="Get Call Details",
    tags=["Collections"],
    description="""
    Retrieve detailed information about a specific call.\n\n
    **Tip:** To see all available call_id values, use the [/collections/call_ids](#/Collections/get_collections_call_ids) endpoint.
    """
)

@router.get(
    "/collections/call/{call_id}",
    summary="Get Call Details",
    tags=["Collections"],
    description="""
    Retrieve detailed information about a specific call.\n\n
    **Tip:** To see all available call_id values, use the [/collections/call_ids](#/Collections/get_collections_call_ids) endpoint.
    """
)
def get_call_details(
    call_id: str = Path(..., description="The call_id to look up."),
    db: Session = Depends(get_db)
):
    call = db.query(CallOutcome).filter(CallOutcome.call_id == call_id).first()
    if not call:
        raise HTTPException(404, "Call ID not found")

    # Get customer info
    customer = db.query(CustomerMasterData).filter(CustomerMasterData.customer_number == call.customer_number).first()
    customer_name = customer.customer_name if customer else None
    phone = None
    email = None
    if customer:
        phone = getattr(customer, 'phone_number', None)
        email = getattr(customer, 'email_address', None)

    # Format response
    return {
        "call_id": call.call_id,
        "case_id": str(call.case_id) if call.case_id else None,
        "customer_number": str(call.customer_number) if call.customer_number else None,
        "customer_name": customer_name,
        "phone": phone,
        "email": email,
        "invoice_numbers": call.invoice_numbers if call.invoice_numbers else [],
        "attempt_number": call.attempt_number,
        "call_start_at": call.call_start_at.isoformat() if call.call_start_at else None,
        "call_end_at": call.call_end_at.isoformat() if call.call_end_at else None,
        "call_status": call.call_status,
        "voice_mail": call.voice_mail,
        "full_transcript": call.full_transcript,
        "call_summary": call.call_summary if call.call_summary else [],
        "call_recording_url": call.call_recording_url,
        "actions_taken": call.call_summary if hasattr(call, 'call_summary') and call.call_summary else []
    }

def build_case_workflow_json(db: Session, case: CollectionQueue, payload: dict):

    # ----------------------------
    # 1. Customer Info
    # ----------------------------
    customer = db.query(CustomerMaster).filter(
        CustomerMaster.customer_id == case.customer_id
    ).first()

    if not customer:
        raise HTTPException(404, "Customer record missing for this case")

    customer_info = {
        "customer_id": str(customer.customer_id),
        "customer_name": customer.customer_name,
        "billing_address": customer.billing_address,
        "contact_name": customer.contact_name,
        "phone_number": customer.phone_number,
        "email_address": customer.email_address,
        "preferred_language": customer.preferred_language,
        "time_zone": customer.time_zone
    }

    # ----------------------------
    # 2. Invoice Info
    # ----------------------------
    invoices = db.query(ARTransaction).filter(
        ARTransaction.customer_id == case.customer_id
    ).all()

    invoice_info = []
    for i in invoices:
        invoice_info.append({
            "document_number": i.document_number,
            "outstanding_balance": float(i.outstanding_balance or 0),
            "due_date": i.due_date.isoformat() if i.due_date else None,
            "days_past_due": i.days_past_due,
            "open_ptp": i.open_ptp,
            "open_dispute": i.open_dispute,
        })

    # ----------------------------
    # 3. Existing call_data
    # ----------------------------
    call_handler = case.call_data or {}
    attempt_number = call_handler.get("attempt_number", 0)

    # ----------------------------
    # 4. Read from payload correctly
    # ----------------------------
    payload_call_failed = payload.get("call_failed")

    # If no call_failed in payload → use existing DB values
    if not payload_call_failed:
        payload_call_failed = case.call_failed or {}

    payload_status = payload_call_failed.get("status")

    # ----------------------------
    # 5. Core Logic
    # ----------------------------
    if payload_status == "failed":
        if attempt_number < 3:
            attempt_number += 1
            call_handler["attempt_number"] = attempt_number

            case.call_failed = payload_call_failed
            case.call_data = call_handler

            flag_modified(case, "call_data")
            flag_modified(case, "call_failed")

            db.commit()
            db.refresh(case)
        else:
            # raise ValueError("attempt_number cannot exceed 3")
            raise HTTPException(
            status_code=400,
            detail="attempt_number cannot exceed 3."
        )    

    else:
        # Update status only
        case.call_failed = payload_call_failed
        flag_modified(case, "call_failed")
        db.commit()

    return {
        "case_id": case.case_id,
        "attempt_number": attempt_number,
        "customer_info": customer_info,
        "invoice_info": invoice_info,
        "call_handler": call_handler,
        "call_failed": payload_call_failed
    }
