
"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID





# ============= Queue List Response Schemas =============

class InvoiceInfo(BaseModel):
    """Invoice information"""
    invoice_no: str
    outstanding_balance: Decimal
    due_date: Optional[date] = None
    days_past_due: Optional[int] = None


class QueueItem(BaseModel):
    """Single queue item response"""
    case_id: str
    customer_number: str
    customer_name: str
    phone: str
    email: str
    region: Optional[str] = None
    invoice_nos: List[str] = Field(default_factory=list)
    outstanding_balance: Decimal
    due_date: Optional[date] = None
    age: Optional[int] = None  # Calculated field: days since due date
    action_status: str
    dunning_stage: str
    time_zone: Optional[str] = None
    multiple_invoice: bool = False
    aging_bucket_category: Optional[str] = None

    class Config:
        from_attributes = True


class QueueListResponse(BaseModel):
    """Response for queue list endpoint"""
    total_records: int
    records: List[QueueItem]

    class Config:
        from_attributes = True


# ============= Case Details Response Schemas =============

class ActionSummary(BaseModel):
    """Summary of an action taken"""
    action_type: str  # PromiseToPay, Escalation, Dispute, etc
    action_id: str
    created_at: Optional[datetime] = None
    details: Optional[Any] = None


class CallDetail(BaseModel):
    """Details of a single call"""
    call_id: str
    attempt_number: Optional[int] = None
    call_start_at: Optional[datetime] = None
    call_end_at: Optional[datetime] = None
    call_status: str
    voice_mail: bool = False
    call_summary: Optional[List[str]] = None
    call_recording_url: Optional[str] = None


class CaseDetailsResponse(BaseModel):
    """Response for case details endpoint"""
    case_id: str
    customer_number: str
    phone: str
    email: str
    region: Optional[str] = None
    invoice_numbers: List[str] = Field(default_factory=list)
    due_date: Optional[date] = None
    outstanding_balance: Decimal
    workflow_steps: Optional[list] = None  # List of dicts: day, label, date, active
    full_transcript: Optional[list] = None  # List of dicts: user/agent turns
    call_summary: Optional[list] = None  # List of summary strings
    actions: Optional[list] = None  # List of dicts (action details)
    call_recording: Optional[str] = None

    class Config:
        from_attributes = True


# ============= Call Details Response Schemas =============

class CallOutcomeResponse(BaseModel):
    """Response for call details endpoint"""
    call_id: str
    case_id: str
    customer_number: str
    customer_name: str
    phone: str
    email: str
    invoice_numbers: List[str] = Field(default_factory=list)
    attempt_number: Optional[int] = None
    call_start_at: Optional[datetime] = None
    call_end_at: Optional[datetime] = None
    call_status: str
    voice_mail: bool = False
    full_transcript: Optional[str] = None
    call_summary: Optional[List[str]] = None
    call_recording_url: Optional[str] = None
    actions_taken: List[ActionSummary] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ============= PromiseToPay Schema =============

class PromiseToPayResponse(BaseModel):
    """Promise to Pay action details"""
    action_id: str
    promised_amount: Optional[Decimal] = None
    promised_date: Optional[date] = None
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ============= Escalation Schema =============

class EscalationResponse(BaseModel):
    """Escalation action details"""
    action_id: str
    escalation_level: str
    escalated_to_role: str
    escalated_to_user: Optional[str] = None
    reason: str
    target_resolution_date: Optional[date] = None
    sla_hours: Optional[int] = None

    class Config:
        from_attributes = True


# ============= Dispute Schema =============

class DisputeResponse(BaseModel):
    """Dispute action details"""
    action_id: str
    dispute_category: str
    description: str
    disputed_amount: Optional[Decimal] = None
    documents_requested: Optional[List[str]] = None
    resolution_code: Optional[str] = None
    resolution_notes: Optional[str] = None

    class Config:
        from_attributes = True


# ============= Document Copy Schema =============

class DocumentCopyResponse(BaseModel):
    """Document Copy action details"""
    action_id: str
    document_type: str
    document_reference: Optional[str] = None
    delivery_channel: str
    delivery_status: str
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============= Partial Payment Schema =============

class PartialPaymentResponse(BaseModel):
    """Partial Payment action details"""
    action_id: str
    amount: Decimal
    payment_date: datetime
    payment_method: str
    reference_number: Optional[str] = None
    allocated_invoice_reference: Optional[str] = None

    class Config:
        from_attributes = True


# ============= Query Parameters =============

class QueueFilterParams(BaseModel):
    """Query filter parameters for queue list"""
    date: Optional[date] = None
    from_date: Optional[date] = Field(None, alias="from")
    to_date: Optional[date] = None
    status: Optional[str] = None
    stage: Optional[str] = None
    due_date: Optional[date] = None
    due_from: Optional[date] = Field(None, alias="duedate_from")
    due_to: Optional[date] = Field(None, alias="duedate_to")
    customer_number: Optional[str] = None
    aging_bucket: Optional[str] = None


# ============= Error Response Schema =============

class ErrorResponse(BaseModel):
    """Standard error response"""
    status_code: int
    message: str
    details: Optional[str] = None

    class Config:
        from_attributes = True
