"""
Agent Workflow Extensions for Call Handling System

This module extends the existing call handling system to support:
1. Precall Agent: Process raw webcollect data and store in precall_cust_data table
2. Caller Agent: Get processed data with call_type-based prompts
3. Postcall Agent: Extract and analyze call transcripts

Reuses existing tables: CustomerMaster, ARTransaction, CollectionQueue
Reuses existing APIs: /call-handle/, /call-workflow/
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CustomerMaster, ARTransaction, CollectionQueue, PrecallCustData, CustCurrentAgent, PostcallCustData
from app.schemas import CollectionQueueCreate
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from pydantic import BaseModel

router = APIRouter()

# ============================================================================
# AGENT DATA SCHEMAS
# ============================================================================

class PrecallAgentInput(BaseModel):
    """Raw data from webcollect database"""
    user_id: str
    user_name: str
    user_phone: str
    user_mail: str
    account_status: str
    preferred_language: str
    preferred_contact_time: str
    agent_contact_allowed: bool
    collector_name: str
    collector_id: str
    billing_address: str
    credit_limit: str  # Will be converted to Decimal
    invoice_amount: str  # Will be converted to Decimal
    short_payment: int
    over_payment: int
    call_type: int
    dispute: str  # Will be converted to Decimal
    payment_terms: str
    status: str
    date: str  # Will be converted to datetime
    notes: List[str]
    audio_recording_enable: bool
    agent_call: bool
    transcript: bool

class PrecallAgentOutput(BaseModel):
    """Output from precall agent - raw data + call_prompt"""
    user_id: str
    user_name: str
    user_phone: str
    user_mail: str
    account_status: str
    preferred_language: str
    preferred_contact_time: str
    agent_contact_allowed: bool
    collector_name: str
    collector_id: str
    billing_address: str
    credit_limit: str
    invoice_amount: str
    short_payment: int
    over_payment: int
    call_type: int
    dispute: str
    payment_terms: str
    status: str
    date: str
    notes: List[str]
    last_notes: str  # Last added note (reference only, not stored in DB)
    audio_recording_enable: bool
    agent_call: bool
    transcript: bool
    call_prompt: str  # Prompt based on call_type (call_1, call_2, etc)
    message: str  # Status message for update/create

class CallAgentinput(BaseModel):
    """Output from precall agent - raw data + call_prompt"""
    user_id: str
    user_name: str
    user_phone: str
    user_mail: str
    account_status: str
    preferred_language: str
    preferred_contact_time: str
    agent_contact_allowed: bool
    collector_name: str
    collector_id: str
    billing_address: str
    credit_limit: str
    invoice_amount: str
    short_payment: int
    over_payment: int
    call_type: int
    dispute: str
    payment_terms: str
    status: str
    date: str
    notes: List[str]
    last_notes: str  # Last added note (reference only, not stored in DB)
    audio_recording_enable: bool
    agent_call: bool
    transcript: bool
    call_prompt: str  # Prompt based on call_type (call_1, call_2, etc)
    transcript_address: Optional[str] = None  # BLOB storage address for transcript
    audio_address: Optional[str] = None  # BLOB storage address for audio recording
    message: str  # Status message for update/create
    message: str  # Status message for update/create

class CallerAgentOutput(BaseModel):
    """Data sent to caller agent - precall output + blob storage addresses"""
    user_id: str
    user_name: str
    user_phone: str
    user_mail: str
    account_status: str
    preferred_language: str
    preferred_contact_time: str
    agent_contact_allowed: bool
    collector_name: str
    collector_id: str
    billing_address: str
    credit_limit: str
    invoice_amount: str
    short_payment: int
    over_payment: int
    call_type: int
    dispute: str
    payment_terms: str
    status: str
    date: str
    notes: List[str]
    last_notes: str
    audio_recording_enable: bool
    agent_call: bool
    transcript: bool
    call_prompt: str
    transcript_address: Optional[str] = None  # BLOB storage address for transcript
    audio_address: Optional[str] = None  # BLOB storage address for audio recording
    message: str  # Status message from precall


class PostcallAgentOutput(BaseModel):
    """Output from postcall agent with AI analysis"""
    user_id: str
    user_name: str
    user_phone: str
    user_mail: str
    account_status: str
    preferred_language: str
    preferred_contact_time: str
    agent_contact_allowed: bool
    collector_name: str
    collector_id: str
    billing_address: str
    credit_limit: str
    invoice_amount: str
    short_payment: int
    over_payment: int
    call_type: int
    dispute: str
    payment_terms: str
    status: str
    date: str
    notes: List[str]
    last_notes: str
    audio_recording_enable: bool
    agent_call: bool
    transcript: bool
    call_prompt: str
    transcript_address: str
    audio_address: str
    action_items: Dict[str, str]  # {"agent_response": str, "user_response": str}
    summary: str  # Call summary (appended to notes list)
    categorization: str  # Call categorization
    message: str  # Status message from precall

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_call_type_prompt(call_type: int) -> str:
    """Return prompt based on call_type per conversation"""
    prompts = {
        1: "call_1",  # First call script - new customer
        2: "call_2",  # Follow-up call - based on last notes
        3: "call_3"   # Additional follow-up
    }
    return prompts.get(call_type, "call_1")

def extract_last_notes(notes: List[str]) -> str:
    """Return only the last added note as string"""
    return notes[-1] if notes and len(notes) > 0 else "NA"

def process_raw_webcollect_data(raw_data: PrecallAgentInput, message: str) -> PrecallAgentOutput:
    """Process raw webcollect data - focus on notes and call_type"""
    last_note = extract_last_notes(raw_data.notes)
    call_prompt = get_call_type_prompt(raw_data.call_type)
    
    return PrecallAgentOutput(
        user_id=raw_data.user_id,
        user_name=raw_data.user_name,
        user_phone=raw_data.user_phone,
        user_mail=raw_data.user_mail,
        account_status=raw_data.account_status,
        preferred_language=raw_data.preferred_language,
        preferred_contact_time=raw_data.preferred_contact_time,
        agent_contact_allowed=raw_data.agent_contact_allowed,
        collector_name=raw_data.collector_name,
        collector_id=raw_data.collector_id,
        billing_address=raw_data.billing_address,
        credit_limit=raw_data.credit_limit,
        invoice_amount=raw_data.invoice_amount,
        short_payment=raw_data.short_payment,
        over_payment=raw_data.over_payment,
        call_type=raw_data.call_type,
        dispute=raw_data.dispute,
        payment_terms=raw_data.payment_terms,
        status=raw_data.status,
        date=raw_data.date,
        notes=raw_data.notes,
        last_notes=last_note,
        audio_recording_enable=raw_data.audio_recording_enable,
        agent_call=raw_data.agent_call,
        transcript=raw_data.transcript,
        call_prompt=call_prompt,
        message=message
    )

def enhance_with_blob_addresses(precall_output: PrecallAgentOutput, 
                               transcript_address: str,
                               audio_address: str) -> CallerAgentOutput:
    """Add BLOB storage addresses to precall output for caller agent"""
    return CallerAgentOutput(
        user_id=precall_output.user_id,
        user_name=precall_output.user_name,
        user_phone=precall_output.user_phone,
        user_mail=precall_output.user_mail,
        account_status=precall_output.account_status,
        preferred_language=precall_output.preferred_language,
        preferred_contact_time=precall_output.preferred_contact_time,
        agent_contact_allowed=precall_output.agent_contact_allowed,
        collector_name=precall_output.collector_name,
        collector_id=precall_output.collector_id,
        billing_address=precall_output.billing_address,
        credit_limit=precall_output.credit_limit,
        invoice_amount=precall_output.invoice_amount,
        short_payment=precall_output.short_payment,
        over_payment=precall_output.over_payment,
        call_type=precall_output.call_type,
        dispute=precall_output.dispute,
        payment_terms=precall_output.payment_terms,
        status=precall_output.status,
        date=precall_output.date,
        notes=precall_output.notes,
        last_notes=precall_output.last_notes,
        audio_recording_enable=precall_output.audio_recording_enable,
        agent_call=precall_output.agent_call,
        transcript=precall_output.transcript,
        call_prompt=precall_output.call_prompt,
        transcript_address=transcript_address,
        audio_address=audio_address
    )


def store_precall_data(raw_data: PrecallAgentInput, customer_id: str, db: Session) -> PrecallCustData:
    """Store raw webcollect data in precall_cust_data table"""
    from decimal import Decimal
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Parse amounts
        credit_limit = Decimal(raw_data.credit_limit.replace('$', '').replace(',', '')) if raw_data.credit_limit else None
        invoice_amount = Decimal(raw_data.invoice_amount.replace('$', '').replace(',', '')) if raw_data.invoice_amount else None
        dispute_amount = Decimal(raw_data.dispute.replace('$', '').replace(',', '')) if raw_data.dispute else None
        
        # Parse date
        parsed_date = datetime.fromisoformat(raw_data.date) if raw_data.date else None
        
        logger.info(f"Storing precall data for customer_id: {customer_id}")
        
        # Create record
        precall_record = PrecallCustData(
            customer_id=uuid.UUID(customer_id),
            user_name=raw_data.user_name,
            user_phone=raw_data.user_phone,
            user_mail=raw_data.user_mail,
            account_status=raw_data.account_status,
            preferred_language=raw_data.preferred_language,
            preferred_contact_time=raw_data.preferred_contact_time,
            agent_contact_allowed=raw_data.agent_contact_allowed,
            collector_name=raw_data.collector_name,
            collector_id=raw_data.collector_id,
            billing_address=raw_data.billing_address,
            credit_limit=credit_limit,
            invoice_amount=invoice_amount,
            short_payment=raw_data.short_payment,
            over_payment=raw_data.over_payment,
            call_type=raw_data.call_type,
            dispute=dispute_amount,
            payment_terms=raw_data.payment_terms,
            status=raw_data.status,
            date=parsed_date,
            notes=raw_data.notes,
            audio_recording_enable=raw_data.audio_recording_enable,
            agent_call=raw_data.agent_call,
            transcript=raw_data.transcript
        )
        
        db.add(precall_record)
        db.commit()
        db.refresh(precall_record)
        logger.info(f"Successfully stored precall data with id: {precall_record.id}")
        return precall_record
        
    except Exception as e:
        logger.error(f"Error storing precall data: {e}")
        db.rollback()
        raise


def update_precall_data(existing_record: PrecallCustData, raw_data: PrecallAgentInput, db: Session) -> PrecallCustData:
    """Update existing precall data record"""
    from decimal import Decimal
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Parse amounts
        credit_limit = Decimal(raw_data.credit_limit.replace('$', '').replace(',', '')) if raw_data.credit_limit else None
        invoice_amount = Decimal(raw_data.invoice_amount.replace('$', '').replace(',', '')) if raw_data.invoice_amount else None
        dispute_amount = Decimal(raw_data.dispute.replace('$', '').replace(',', '')) if raw_data.dispute else None
        
        # Parse date
        parsed_date = datetime.fromisoformat(raw_data.date) if raw_data.date else None
        
        logger.info(f"Updating precall data for customer_id: {existing_record.customer_id}")
        
        # Update record
        existing_record.user_name = raw_data.user_name
        existing_record.user_phone = raw_data.user_phone
        existing_record.user_mail = raw_data.user_mail
        existing_record.account_status = raw_data.account_status
        existing_record.preferred_language = raw_data.preferred_language
        existing_record.preferred_contact_time = raw_data.preferred_contact_time
        existing_record.agent_contact_allowed = raw_data.agent_contact_allowed
        existing_record.collector_name = raw_data.collector_name
        existing_record.collector_id = raw_data.collector_id
        existing_record.billing_address = raw_data.billing_address
        existing_record.credit_limit = credit_limit
        existing_record.invoice_amount = invoice_amount
        existing_record.short_payment = raw_data.short_payment
        existing_record.over_payment = raw_data.over_payment
        existing_record.call_type = raw_data.call_type
        existing_record.dispute = dispute_amount
        existing_record.payment_terms = raw_data.payment_terms
        existing_record.status = raw_data.status
        existing_record.date = parsed_date
        existing_record.notes = raw_data.notes
        existing_record.audio_recording_enable = raw_data.audio_recording_enable
        existing_record.agent_call = raw_data.agent_call
        existing_record.transcript = raw_data.transcript
        existing_record.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(existing_record)
        logger.info(f"Successfully updated precall data with id: {existing_record.id}")
        return existing_record
        
    except Exception as e:
        logger.error(f"Error updating precall data: {e}")
        db.rollback()
        raise


def validate_customer_invoice(customer_id: str, invoice_amount: str, db: Session) -> bool:
    """Validate if customer has an invoice with the specified outstanding balance amount"""
    # Parse the invoice amount
    try:
        from decimal import Decimal
        amount = Decimal(invoice_amount.replace('$', '').replace(',', ''))
        # Check if customer has an AR transaction with this amount
        invoice_count = db.query(ARTransaction).filter(
            ARTransaction.customer_id == customer_id,
            ARTransaction.outstanding_balance == amount
        ).count()
        return invoice_count > 0
    except Exception:
        return False


def analyze_transcript(transcript_address: str) -> Dict[str, Any]:
    """Mock function to analyze transcript - replace with actual AI analysis"""
    # In real implementation, this would:
    # 1. Fetch transcript from blob storage
    # 2. Send to AI for analysis
    # 3. Return structured results

    return {
        "action_items": {"Agent": "Agent_Responce", "User": "User_Responce"},
        "summary": "Summary of the call",
        "categorization": "categorization of the call"
    }

# ============================================================================
# AGENT ENDPOINTS
# ============================================================================

@router.post("/precall-agent/", response_model=PrecallAgentOutput)
def precall_agent_endpoint(raw_data: PrecallAgentInput, db: Session = Depends(get_db)):
    """
    Precall Agent: Process raw webcollect data
    
    Per conversation:
    - Focuses on: notes and call_type
    - Assigns call_prompt based on call_type
    - If call_type = 1: prompt_1 (first call script)
    - If call_type = 2: prompt_2 (follow-up using last notes)
    - Checks if record exists: if yes, updates and returns update message
    - If no record, validates customer has invoice with matching amount in ARTransaction
    - Returns precall output with call_prompt and status message
    """
    # Validate customer exists
    customer = db.query(CustomerMaster).filter(
        CustomerMaster.customer_id == raw_data.user_id
    ).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found in database")

    # Check if precall record already exists
    existing_record = db.query(PrecallCustData).filter(
        PrecallCustData.customer_id == raw_data.user_id
    ).first()

    if existing_record:
        # Update existing record
        updated_data = update_precall_data(existing_record, raw_data, db)
        message = f"Customer ID {raw_data.user_id} details updated"
    else:
        # Validate customer-invoice combination
        has_invoice = validate_customer_invoice(raw_data.user_id, raw_data.invoice_amount, db)
        if not has_invoice:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid matching between customer_id {raw_data.user_id} and invoice"
            )
        # Store new record
        stored_data = store_precall_data(raw_data, raw_data.user_id, db)
        message = f"New record created for customer ID {raw_data.user_id}"

    # Process the raw data
    precall_output = process_raw_webcollect_data(raw_data, message)

    return precall_output

@router.post("/caller-agent/", response_model=CallerAgentOutput)
def caller_agent_endpoint(
    caller_input: CallAgentinput,
    db: Session = Depends(get_db)
):
    """
    Caller Agent: Add BLOB storage addresses for transcript and audio

    Per transcript conversation:
    - Receives caller agent input (may already have blob addresses)
    - Adds transcript_address and audio_address if not present
    - Stores complete record in cust_current_agent table
    - Agent uses these to access transcript/audio during/after call
    """
    # Check if blob addresses are already present, if not add them
    transcript_address = caller_input.transcript_address if caller_input.transcript_address else "https://blob.storage/transcript/{id}.txt"
    audio_address = caller_input.audio_address if caller_input.audio_address else "https://blob.storage/audio/{id}.wav"
    
    # Enhance with BLOB storage addresses
    response = CallerAgentOutput(
        user_id=caller_input.user_id,
        user_name=caller_input.user_name,
        user_phone=caller_input.user_phone,
        user_mail=caller_input.user_mail,
        account_status=caller_input.account_status,
        preferred_language=caller_input.preferred_language,
        preferred_contact_time=caller_input.preferred_contact_time,
        agent_contact_allowed=caller_input.agent_contact_allowed,
        collector_name=caller_input.collector_name,
        collector_id=caller_input.collector_id,
        billing_address=caller_input.billing_address,
        credit_limit=caller_input.credit_limit,
        invoice_amount=caller_input.invoice_amount,
        short_payment=caller_input.short_payment,
        over_payment=caller_input.over_payment,
        call_type=caller_input.call_type,
        dispute=caller_input.dispute,
        payment_terms=caller_input.payment_terms,
        status=caller_input.status,
        date=caller_input.date,
        notes=caller_input.notes,
        last_notes=caller_input.last_notes,
        audio_recording_enable=caller_input.audio_recording_enable,
        agent_call=caller_input.agent_call,
        transcript=caller_input.transcript,
        call_prompt=caller_input.call_prompt,
        transcript_address=transcript_address,
        audio_address=audio_address,
        message=caller_input.message
    )

    # Store complete record in cust_current_agent table
    try:
        from decimal import Decimal
        import uuid
        
        # Parse amounts
        credit_limit = Decimal(caller_input.credit_limit.replace('$', '').replace(',', '')) if caller_input.credit_limit else None
        invoice_amount = Decimal(caller_input.invoice_amount.replace('$', '').replace(',', '')) if caller_input.invoice_amount else None
        dispute_amount = Decimal(caller_input.dispute.replace('$', '').replace(',', '')) if caller_input.dispute else None
        
        # Parse date
        parsed_date = datetime.fromisoformat(caller_input.date) if caller_input.date else None
        
        # Create record in cust_current_agent table
        current_agent_record = CustCurrentAgent(
            customer_id=uuid.UUID(caller_input.user_id),
            user_name=caller_input.user_name,
            user_phone=caller_input.user_phone,
            user_mail=caller_input.user_mail,
            account_status=caller_input.account_status,
            preferred_language=caller_input.preferred_language,
            preferred_contact_time=caller_input.preferred_contact_time,
            agent_contact_allowed=caller_input.agent_contact_allowed,
            collector_name=caller_input.collector_name,
            collector_id=caller_input.collector_id,
            billing_address=caller_input.billing_address,
            credit_limit=credit_limit,
            invoice_amount=invoice_amount,
            short_payment=caller_input.short_payment,
            over_payment=caller_input.over_payment,
            call_type=caller_input.call_type,
            dispute=dispute_amount,
            payment_terms=caller_input.payment_terms,
            status=caller_input.status,
            date=parsed_date,
            notes=caller_input.notes,
            audio_recording_enable=caller_input.audio_recording_enable,
            agent_call=caller_input.agent_call,
            transcript=caller_input.transcript,
            transcript_address=response.transcript_address,
            audio_address=response.audio_address
        )
        
        db.add(current_agent_record)
        db.commit()
        db.refresh(current_agent_record)
        
    except Exception as e:
        db.rollback()
        # Log error but don't fail the request - caller agent should still return response
        print(f"Error storing current agent data: {e}")

    return response

@router.post("/postcall-agent/", response_model=PostcallAgentOutput)
def postcall_agent_endpoint(
    caller_data: PostcallAgentOutput,
    db: Session = Depends(get_db)
):
    """
    Postcall Agent: Extract transcript and analyze call

    Per transcript conversation:
    - Receives caller agent output (contains transcript_address and audio_address)
    - Extracts transcript from BLOB storage
    - Generates: action_items, summary, categorization
    - Summary is appended to notes list for next call reference
    """
    # Mock AI analysis of the transcript
    analysis = analyze_transcript(caller_data.transcript_address)

    # Build output object
    response = PostcallAgentOutput(
        user_id=caller_data.user_id,
        user_name=caller_data.user_name,
        user_phone=caller_data.user_phone,
        user_mail=caller_data.user_mail,
        account_status=caller_data.account_status,
        preferred_language=caller_data.preferred_language,
        preferred_contact_time=caller_data.preferred_contact_time,
        agent_contact_allowed=caller_data.agent_contact_allowed,
        collector_name=caller_data.collector_name,
        collector_id=caller_data.collector_id,
        billing_address=caller_data.billing_address,
        credit_limit=caller_data.credit_limit,
        invoice_amount=caller_data.invoice_amount,
        short_payment=caller_data.short_payment,
        over_payment=caller_data.over_payment,
        call_type=caller_data.call_type,
        dispute=caller_data.dispute,
        payment_terms=caller_data.payment_terms,
        status=caller_data.status,
        date=caller_data.date,
        notes=caller_data.notes,
        last_notes=caller_data.last_notes,
        audio_recording_enable=caller_data.audio_recording_enable,
        agent_call=caller_data.agent_call,
        transcript=caller_data.transcript,
        call_prompt=caller_data.call_prompt,
        transcript_address=caller_data.transcript_address,
        audio_address=caller_data.audio_address,
        action_items=analysis["action_items"],
        summary=analysis["summary"],
        categorization=analysis["categorization"],
        message=caller_data.message
    )

    # Store postcall data in postcall_cust_data
    try:
        from decimal import Decimal
        import uuid

        credit_limit = Decimal(caller_data.credit_limit.replace('$', '').replace(',', '')) if caller_data.credit_limit else None
        invoice_amount = Decimal(caller_data.invoice_amount.replace('$', '').replace(',', '')) if caller_data.invoice_amount else None
        dispute_amount = Decimal(caller_data.dispute.replace('$', '').replace(',', '')) if caller_data.dispute else None
        parsed_date = datetime.fromisoformat(caller_data.date) if caller_data.date else None

        postcall_record = PostcallCustData(
            customer_id=uuid.UUID(caller_data.user_id),
            user_name=caller_data.user_name,
            user_phone=caller_data.user_phone,
            user_mail=caller_data.user_mail,
            account_status=caller_data.account_status,
            preferred_language=caller_data.preferred_language,
            preferred_contact_time=caller_data.preferred_contact_time,
            agent_contact_allowed=caller_data.agent_contact_allowed,
            collector_name=caller_data.collector_name,
            collector_id=caller_data.collector_id,
            billing_address=caller_data.billing_address,
            credit_limit=credit_limit,
            invoice_amount=invoice_amount,
            short_payment=caller_data.short_payment,
            over_payment=caller_data.over_payment,
            call_type=caller_data.call_type,
            dispute=dispute_amount,
            payment_terms=caller_data.payment_terms,
            status=caller_data.status,
            date=parsed_date,
            notes=caller_data.notes,
            audio_recording_enable=caller_data.audio_recording_enable,
            agent_call=caller_data.agent_call,
            transcript=caller_data.transcript,
            call_prompt=caller_data.call_prompt,
            transcript_address=caller_data.transcript_address,
            audio_address=caller_data.audio_address,
            action_items=analysis["action_items"],
            summary=analysis["summary"],
            categorization=analysis["categorization"],
            message=caller_data.message
        )

        db.add(postcall_record)
        db.commit()
        db.refresh(postcall_record)

    except Exception as e:
        db.rollback()
        print(f"Error storing postcall data: {e}")

    return response