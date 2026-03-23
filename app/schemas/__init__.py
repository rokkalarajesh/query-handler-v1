"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import  Optional, List, Tuple, Any, Dict, Literal
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
import uuid


from pydantic import BaseModel, Field, ConfigDict, field_validator, field_serializer




US_TZ = (
    'America/New_York', 'America/Detroit', 'America/Indiana/Indianapolis',
    'America/Indiana/Marengo', 'America/Indiana/Vincennes', 'America/Indiana/Winamac',
    'America/Indiana/Knox', 'America/Indiana/Tell_City', 'America/Kentucky/Louisville',
    'America/Kentucky/Monticello', 'America/Chicago', 'America/Menominee',
    'America/Denver', 'America/Boise', 'America/Phoenix', 'America/Los_Angeles',
    'America/Anchorage', 'America/Juneau', 'America/Nome', 'America/Metlakatla',
    'America/Sitka', 'America/Yakutat', 'America/Adak', 'Pacific/Honolulu',
)
US_TZ_LIT = Literal[
    'America/New_York', 'America/Detroit', 'America/Indiana/Indianapolis',
    'America/Indiana/Marengo', 'America/Indiana/Vincennes', 'America/Indiana/Winamac',
    'America/Indiana/Knox', 'America/Indiana/Tell_City', 'America/Kentucky/Louisville',
    'America/Kentucky/Monticello', 'America/Chicago', 'America/Menominee',
    'America/Denver', 'America/Boise', 'America/Phoenix', 'America/Los_Angeles',
    'America/Anchorage', 'America/Juneau', 'America/Nome', 'America/Metlakatla',
    'America/Sitka', 'America/Yakutat', 'America/Adak', 'Pacific/Honolulu',
]


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


# ============= Placeholders for Colleague Module Schemas =============
# class CallNote(BaseModel):
#     note_id: Optional[str] = None
#     content: Optional[str] = None
#     created_at: Optional[datetime] = None

# class InvoiceItem(BaseModel):
#     document_number: Optional[str] = None
#     amount: Optional[Decimal] = None

# class CallFailed(BaseModel):
#     reason: Optional[str] = None
#     timestamp: Optional[datetime] = None

# class CallData(BaseModel):
#     call_id: Optional[str] = None
#     data: Optional[Any] = None

# class CollectionQueueCreate(BaseModel):
#     customer_number: Optional[UUID] = None
#     invoice_nos: Optional[list] = None

# class CollectionQueueSlimOut(BaseModel):
#     case_id: Optional[str] = None
#     status: Optional[str] = None


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



class CallNote(BaseModel):
    author: Optional[str] = Field(default=None, description="Who added the note")
    note: str
    created_at: Optional[datetime] = None  # server will fill if missing

class InvoiceItem(BaseModel):
    document_number: Optional[str] = Field(None, alias="inovice_n")
    outstanding_balance: Optional[Decimal] = None
    overdue_status: Optional[str] = None
    due_date: Optional[datetime] = None
    days_past_due: Optional[int] = None
    purchase_order_number: Optional[str] = Field(None, alias="purchase_order_num")
    order_date: Optional[datetime] = None

    open_ptp: Optional[bool] = None
    open_ptp_date: Optional[datetime] = None
    broken_ptp_flag: Optional[bool] = Field(None, alias="broken_ptp_flg")
    broken_ptp_amount: Optional[Decimal] = None
    broken_ptp_date: Optional[datetime] = None

    open_dispute: Optional[bool] = None
    closed_dispute_status: Optional[str] = None
    issued_credits: Optional[Decimal] = Field(None, alias="isseues_credits")

    model_config = ConfigDict(populate_by_name=True)

class CallFailedSummary(BaseModel):
    total_errors: int
    error_categories: List[str]

class CallFailed(BaseModel):
    status: str
    errors: List[Any]
    summary: CallFailedSummary

class CallData(BaseModel):
    attempt_number: Optional[int] = None
    call_start_at: Optional[datetime] = None
    call_end_at: Optional[datetime] = None
    call_status: Optional[str] = None
    Voice_mail: Optional[bool] = Field(default=None, alias="Voice mail")
    Transcript: Optional[dict] = None
    Actions: Optional[dict] = None

    # <-- VALIDATION RULE FOR ATTEMPT_NUMBER -->
    @field_validator("attempt_number", mode="before")
    def validate_attempt_number(cls, v):
        # Treat None as 1
        if v is None:
            return 1
        
        # Ensure it's int
        try:
            num = int(v)
        except:
            raise ValueError("attempt_number must be a valid integer")

        # Validate boundaries
        if num < 1:
            raise ValueError("attempt_number cannot be less than 1")
        if num > 3:
            raise ValueError("attempt_number cannot exceed 3")

        return num

    model_config = ConfigDict(populate_by_name=True)

class CollectionQueueBase(BaseModel):
    customer_id: uuid.UUID
    uniqid: Optional[str] = Field(default=None)

    invoice_numbers: Optional[List[InvoiceItem]] = None
    multiple_invoice: Optional[bool] = None

    aging_bucket: Optional[str] = None
    priority: Optional[int] = None
    due_at: Optional[datetime] = None

    call_notes: Optional[List[CallNote]] = None
    call_type: Optional[str] = None

    activity_status: Optional[bool] = None
    # activity_empty_reason: Optional[str] = None
    dnc_status: Optional[bool] = None
    # dnc_reason_yes: Optional[str] = None
    record_consent: Optional[bool] = None

    customer_name: Optional[str] = None
    billing_address: Optional[str] = None
    contact_name: Optional[str] = None
    phone_number: Optional[str] = None
    email_address: Optional[str] = None
    preferred_language: Optional[str] = None

    calling_window: Optional[Tuple[datetime, datetime]] = Field(
        default=None,
        description="Local window tuple (start, end) interpreted in `time_zone`"
    )
    time_zone: Optional[US_TZ_LIT] = Field(
        default=None,
        description="US IANA time zone name (e.g., America/New_York)"
    )

    call_failed: Optional[CallFailed] = Field(
        default=None,
        validation_alias="Call_failed",
        serialization_alias="Call_failed",
        description="Structured validation failure info passed through to response"
    )

    call_data: Optional[CallData | Dict[str, Any]] = Field(
        default=None,
        description="Call metadata (attempt number, start/end, status, voicemail flag)"
    )

    @field_validator("multiple_invoice", mode="before")
    @classmethod
    def infer_multiple_invoice(cls, v, info):
        if v is not None:
            return v
        inv = info.data.get("invoice_numbers")
        if inv is None:
            return None
        try:
            return len(inv) > 1
        except Exception:
            return None

    @field_validator("calling_window")
    @classmethod
    def check_window_bounds(cls, v):
        if v is None:
            return v
        start, end = v
        if start is None or end is None:
            raise ValueError("calling_window must contain (start, end)")
        if end <= start:
            raise ValueError("calling_window end must be greater than start")
        return v

class CollectionQueueCreate(CollectionQueueBase):
    pass

class CollectionQueueSlimOut(BaseModel):
    case_id: str
    customer_id: uuid.UUID

    # customer info
    customer_name: Optional[str] = None
    billing_address: Optional[str] = None
    contact_name: Optional[str] = None
    phone_number: Optional[str] = None
    email_address: Optional[str] = None

    preferred_language: Optional[str] = None
    preferred_contact_hours: Optional[List[datetime]] = None
    time_zone: Optional[str] = None

    # call info
    attempt_number: Optional[int] = None
    multiple_invoice: Optional[bool] = None

    call_data: Optional[dict] = None
    call_failed: Optional[dict] = None

    @field_serializer("preferred_contact_hours")
    def serialize_hours(self, v):
        if v is None:
            return None
        if isinstance(v, (tuple, list)):
            return [v[0], v[1]]
        # psycopg2 tsrange
        return [v.lower, v.upper]

    @field_validator("preferred_contact_hours", mode="before")
    @classmethod
    def convert_calling_window(cls, v):
        if v is None:
            return None
        try:
            return [v.lower, v.upper]
        except Exception:
            return v

    model_config = ConfigDict(from_attributes=True)
