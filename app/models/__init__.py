"""
SQLAlchemy models for collections management system
"""
from sqlalchemy import Column, String, Numeric, DateTime, Boolean, Integer, Date, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSRANGE
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, CITEXT, TSRANGE
from sqlalchemy import Column, String, Numeric, DateTime, Boolean, Integer, Date, ForeignKey, JSON, Text, Index, UniqueConstraint, Numeric 



class CustomerMasterData(Base):
    """Customer Master Data Table"""
    __tablename__ = "customer_master_data"

    customer_number = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_name = Column(String(255), nullable=False)
    account_status = Column(String(50), nullable=False)  # Active/Inactive
    billing_address = Column(String(500))
    contact_name = Column(String(255))
    phone_number = Column(String(20), nullable=False)
    email_address = Column(String(255), nullable=False)
    preferred_language = Column(String(50))
    preferred_contact_hours = Column(String(100))
    agent_contact_allowed = Column(Boolean, default=True)
    account_manager_name = Column(String(255))
    collector_name = Column(String(255))
    collector_phone_number = Column(String(20))
    collector_id = Column(String(50))
    credit_limit = Column(Numeric(18, 2))
    payment_term = Column(String(100))
    billing_method = Column(String(100))
    total_open_balance = Column(Numeric(18, 2), default=0)
    total_overdue_balance = Column(Numeric(18, 2), default=0)
    parent_customer_id = Column(UUID(as_uuid=True))
    dnc_status = Column(Boolean, default=False)  # Do Not Call
    record_consent = Column(Boolean, default=False)
    calling_window = Column(TSRANGE)
    time_zone = Column(String(50), default="IST")

    # Relationships
    call_queues = relationship("CallQueue", back_populates="customer")
    invoices = relationship("InvoiceBalanceTable", back_populates="customer")


class InvoiceBalanceTable(Base):
    """Invoice Balance Table for Transaction Info"""
    __tablename__ = "invoice_balance_table"

    invoice_no = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_number = Column(UUID(as_uuid=True), ForeignKey("customer_master_data.customer_number"), nullable=False)
    document_number = Column(String(100), nullable=False)
    document_type = Column(String(50))  # invoice, credit, adjustment
    document_date = Column(Date)
    invoice_amount = Column(Numeric(18, 2), nullable=False)
    outstanding_balance = Column(Numeric(18, 2), nullable=False)
    document_status = Column(String(50))  # current, due, overdue
    due_date = Column(Date)
    days_past_due = Column(Integer)
    purchase_order_number = Column(String(100))
    order_date = Column(Date)
    delivery_date = Column(Date)
    open_ptp = Column(Boolean, default=False)
    open_ptp_date = Column(Date)
    broken_ptp_flag = Column(Boolean, default=False)
    broken_ptp_amount = Column(Numeric(18, 2))
    broken_ptp_date = Column(Date)
    open_dispute = Column(Boolean, default=False)
    closed_dispute = Column(Boolean, default=False)
    closed_dispute_status = Column(String(50))  # Approved/Rejected
    issued_credits = Column(String(500))
    applied_payment_date = Column(Date)
    applied_payment_amount = Column(Numeric(18, 2))

    # Relationships
    customer = relationship("CustomerMasterData", back_populates="invoices")


class CallQueue(Base):
    """Collection Queue Table"""
    __tablename__ = "call_queue"

    case_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_number = Column(UUID(as_uuid=True), ForeignKey("customer_master_data.customer_number"), nullable=False)
    invoice_nos = Column(JSONB)  # List of invoice numbers
    multiple_invoice = Column(Boolean, default=False)
    aging_bucket_category = Column(String(50))  # all >60 days, >90 days
    call_type = Column(String(50))  # Call1, Call2
    call_attempted = Column(Boolean, default=False)
    action_status = Column(String(100))  # Status like PromiseToPay, Failed, etc
    queue_date = Column(Date, nullable=False)
    dunning_stage = Column(String(100))  # Dunning stage label (no FK relationship)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("CustomerMasterData", back_populates="call_queues")
    call_outcomes = relationship("CallOutcome", back_populates="queue_entry")


class DunningStage(Base):
    """Dunning Stage Configuration"""
    __tablename__ = "dunning_stage"

    stage_id = Column(String(50), primary_key=True)
    stage_day = Column(Integer)
    stage_label = Column(String(100), unique=True, nullable=False)
    stage_date = Column(Date)
    stage_active = Column(Boolean, default=True)


class CallOutcome(Base):
    """Call Outcome Table"""
    __tablename__ = "call_outcome"

    call_id = Column(String(255), primary_key=True)
    customer_number = Column(UUID(as_uuid=True), ForeignKey("customer_master_data.customer_number"))
    case_id = Column(UUID(as_uuid=True), ForeignKey("call_queue.case_id"))
    invoice_numbers = Column(JSONB)  # List of invoice numbers
    attempt_number = Column(Integer)
    call_start_at = Column(DateTime)
    call_end_at = Column(DateTime)
    call_status = Column(String(100))  # Success, No Answer, Busy, Disconnected
    voice_mail = Column(Boolean, default=False)
    full_transcript = Column(Text)
    call_summary = Column(JSONB)  # Array of summaries
    call_recording_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    queue_entry = relationship("CallQueue", back_populates="call_outcomes")


class PromiseToPay(Base):
    """Promise to Pay Action"""
    __tablename__ = "promise_to_pay"

    action_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(String(255), ForeignKey("call_outcome.call_id"))
    promised_amount = Column(Numeric(18, 2))
    promised_date = Column(Date)
    payment_method = Column(String(50))  # BankTransfer, UPI, Check
    reference_number = Column(String(100))
    notes = Column(Text)


class Escalation(Base):
    """Escalation Action"""
    __tablename__ = "escalation"

    action_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(String(255), ForeignKey("call_outcome.call_id"))
    escalation_level = Column(String(50))  # L1, L2, L3, Executive
    escalated_to_role = Column(String(100))
    escalated_to_user = Column(String(100))
    reason = Column(Text)
    target_resolution_date = Column(Date)
    sla_hours = Column(Integer)


class Dispute(Base):
    """Dispute Action"""
    __tablename__ = "dispute"

    action_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(String(255), ForeignKey("call_outcome.call_id"))
    dispute_category = Column(String(100))  # Pricing, Tax, Quantity, PO mismatch
    description = Column(Text)
    disputed_amount = Column(Numeric(18, 2))
    documents_requested = Column(JSONB)
    resolution_code = Column(String(50))  # Adjusted, Rejected, PendingDocs, Credited
    resolution_notes = Column(Text)


class DocumentCopy(Base):
    """Document Copy Action"""
    __tablename__ = "document_copy"

    action_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(String(255), ForeignKey("call_outcome.call_id"))
    document_type = Column(String(50))  # Invoice, SOA, Credit Note, Contract, PO
    document_reference = Column(String(100))
    delivery_channel = Column(String(50))  # Email, Portal, WhatsApp, Internal
    delivery_status = Column(String(50))  # Pending, Sent, Failed
    sent_at = Column(DateTime)


class PartialPayment(Base):
    """Partial Payment Action"""
    __tablename__ = "partial_payment"

    action_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(String(255), ForeignKey("call_outcome.call_id"))
    amount = Column(Numeric(18, 2), nullable=False)
    payment_date = Column(DateTime)
    payment_method = Column(String(50))  # UPI, BankTransfer, Check, Cash
    reference_number = Column(String(100))
    allocated_invoice_reference = Column(String(100))
    linked_ptp_action_id = Column(UUID(as_uuid=True))


class DoubtfulReceivable(Base):
    """Doubtful Receivable Action"""
    __tablename__ = "doubtful_receivable"

    action_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(String(255), ForeignKey("call_outcome.call_id"))
    reason = Column(Text)
    aging_bucket_at_flag = Column(String(50))  # 90+, 120+, 180+
    provision_percentage = Column(Numeric(5, 2))
    effective_from = Column(Date)
    review_date = Column(Date)


class CreditRequest(Base):
    """Credit Request Action"""
    __tablename__ = "credit_request"

    action_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(String(255), ForeignKey("call_outcome.call_id"))
    request_type = Column(String(50))  # Full, Partial, Tax Correction, Other
    requested_amount = Column(Numeric(18, 2))
    requested_percentage = Column(Numeric(5, 2))
    basis = Column(Text)
    related_document_reference = Column(String(100))
    approval_status = Column(String(50))  # Pending, Approved, Rejected
    approval_date = Column(Date)
    approver_role = Column(String(100))


class OtherCustomerRequest(Base):
    """Other Customer Request Action"""
    __tablename__ = "other_customer_request"

    action_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(String(255), ForeignKey("call_outcome.call_id"))
    request_category = Column(String(100))  # AddressUpdate, GSTUpdate, ContactUpdate, POShare, Other
    description = Column(Text)
    due_by = Column(Date)
    completed_at = Column(Date)


class CustomerMaster(Base):
    __tablename__ = "customer_master"

    customer_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(Text, nullable=False)
    customer_name = Column(Text, nullable=False)

    account_status = Column(Text, nullable=True)
    billing_address = Column(Text, nullable=True)
    contact_name = Column(Text, nullable=True)
    phone_number = Column(Text, nullable=True)
    email_address = Column(CITEXT, nullable=True)

    preferred_language = Column(Text, nullable=True)
    preferred_contact_hours = Column(Text, nullable=True)
    agent_contact_allowed = Column(Boolean, nullable=True)
    account_manager_name = Column(Text, nullable=True)
    collector_name = Column(Text, nullable=True)
    collector_phone_number = Column(Text, nullable=True)
    collector_id = Column(Text, nullable=True)
    credit_limit = Column(Numeric(18, 2), nullable=True)
    payment_term = Column(Text, nullable=True)
    billing_method = Column(Text, nullable=True)
    total_open_balance = Column(Numeric(18, 2), nullable=True)
    total_overdue_balance = Column(Numeric(18, 2), nullable=True)
    dnc_status = Column(Boolean, nullable=True)
    record_consent = Column(Boolean, nullable=True)
    calling_window = Column(Text, nullable=True)
    time_zone = Column(Text, nullable=True)

class ARTransaction(Base):
    __tablename__ = "ar_transactions"

    transaction_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PG_UUID(as_uuid=True), ForeignKey("customer_master.customer_id"), nullable=False)

    document_number = Column(Text, nullable=False)
    document_type = Column(Text, nullable=True)
    document_date = Column(DateTime, nullable=True)
    original_amount = Column(Numeric(18, 2), nullable=True)
    outstanding_balance = Column(Numeric(18, 2), nullable=True)
    document_status = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    days_past_due = Column(Integer, nullable=True)
    purchase_order_number = Column(Text, nullable=True)
    order_date = Column(DateTime, nullable=True)
    delivery_date = Column(DateTime, nullable=True)

    open_ptp = Column(Boolean, nullable=True)
    open_ptp_date = Column(DateTime, nullable=True)
    broken_ptp_flag = Column(Boolean, nullable=True)
    broken_ptp_amount = Column(Numeric(18, 2), nullable=True)
    broken_ptp_date = Column(DateTime, nullable=True)

    open_dispute = Column(Boolean, nullable=True)
    closed_dispute = Column(Boolean, nullable=True)
    closed_dispute_status = Column(Text, nullable=True)

    issued_credits = Column(Numeric(18, 2), nullable=True)
    applied_payment_date = Column(DateTime, nullable=True)
    applied_payment_amount = Column(Numeric(18, 2), nullable=True)


class CollectionQueue(Base):
    __tablename__ = "collection_queue"

    case_id = Column(Text, primary_key=True)
    tenant_id = Column(Text, nullable=False)
    customer_id = Column(PG_UUID(as_uuid=True), ForeignKey("customer_master.customer_id"), nullable=False)

    uniqid = Column(Text, nullable=False)

    invoice_numbers = Column(JSONB, nullable=True)
    multiple_invoice = Column(Boolean, nullable=True)

    aging_bucket = Column(Text, nullable=True)
    priority = Column(Integer, nullable=True)
    due_at = Column(DateTime, nullable=True)

    call_notes = Column(JSONB, nullable=True)
    call_type = Column(Integer, nullable=True, server_default="1")

    activity_status = Column(Boolean, nullable=True)
    # activity_empty_reason = Column(Text, nullable=True)
    dnc_status = Column(Boolean, nullable=True)
    # dnc_reason_yes = Column(Text, nullable=True)
    record_consent = Column(Boolean, nullable=True)

    calling_window = Column(TSRANGE, nullable=True)
    time_zone = Column(Text, nullable=True)

    customer_name = Column(Text, nullable=True)
    billing_address = Column(Text, nullable=True)
    contact_name = Column(Text, nullable=True)
    phone_number = Column(Text, nullable=True)
    email_address = Column(Text, nullable=True)
    preferred_language = Column(Text, nullable=True)

    call_data = Column(JSONB, nullable=True)
    call_failed = Column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "customer_id", "uniqid", name="uq_collection_case_key"),
        Index("ix_collection_queue_customer", "tenant_id", "customer_id"),
        Index("ix_collection_queue_status", "activity_status"),
        Index("ix_collection_queue_due", "due_at"),
    )

    customer = relationship("CustomerMaster")



class PrecallCustData(Base):
    """Precall Customer Data Table - stores raw webcollect data"""
    __tablename__ = "precall_cust_data"
 
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PG_UUID(as_uuid=True), ForeignKey("customer_master.customer_id"), nullable=False)
    user_name = Column(Text, nullable=False)
    user_phone = Column(Text, nullable=True)
    user_mail = Column(CITEXT, nullable=True)
    account_status = Column(Text, nullable=True)
    preferred_language = Column(Text, nullable=True)
    preferred_contact_time = Column(Text, nullable=True)
    agent_contact_allowed = Column(Boolean, nullable=True)
    collector_name = Column(Text, nullable=True)
    collector_id = Column(Text, nullable=True)
    billing_address = Column(Text, nullable=True)
    credit_limit = Column(Numeric(18, 2), nullable=True)
    invoice_amount = Column(Numeric(18, 2), nullable=True)
    short_payment = Column(Integer, nullable=True)
    over_payment = Column(Integer, nullable=True)
    call_type = Column(Integer, nullable=True)
    dispute = Column(Numeric(18, 2), nullable=True)
    payment_terms = Column(Text, nullable=True)
    status = Column(Text, nullable=True)
    date = Column(DateTime, nullable=True)
    notes = Column(JSONB, nullable=True)  # List of strings
    audio_recording_enable = Column(Boolean, nullable=True)
    agent_call = Column(Boolean, nullable=True)
    transcript = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
 
    # Relationships
    customer = relationship("CustomerMaster")
 
 
class CustCurrentAgent(Base):
    """Current Agent Data Table - stores precall data plus blob addresses"""
    __tablename__ = "cust_current_agent"
 
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PG_UUID(as_uuid=True), ForeignKey("customer_master.customer_id"), nullable=False)
    user_name = Column(Text, nullable=False)
    user_phone = Column(Text, nullable=True)
    user_mail = Column(CITEXT, nullable=True)
    account_status = Column(Text, nullable=True)
    preferred_language = Column(Text, nullable=True)
    preferred_contact_time = Column(Text, nullable=True)
    agent_contact_allowed = Column(Boolean, nullable=True)
    collector_name = Column(Text, nullable=True)
    collector_id = Column(Text, nullable=True)
    billing_address = Column(Text, nullable=True)
    credit_limit = Column(Numeric(18, 2), nullable=True)
    invoice_amount = Column(Numeric(18, 2), nullable=True)
    short_payment = Column(Integer, nullable=True)
    over_payment = Column(Integer, nullable=True)
    call_type = Column(Integer, nullable=True)
    dispute = Column(Numeric(18, 2), nullable=True)
    payment_terms = Column(Text, nullable=True)
    status = Column(Text, nullable=True)
    date = Column(DateTime, nullable=True)
    notes = Column(JSONB, nullable=True)  # List of strings
    audio_recording_enable = Column(Boolean, nullable=True)
    agent_call = Column(Boolean, nullable=True)
    transcript = Column(Boolean, nullable=True)
    # Additional fields for blob storage addresses
    transcript_address = Column(Text, nullable=True)
    audio_address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
 
    # Relationships
    customer = relationship("CustomerMaster")
 
 
class PostcallCustData(Base):
    """Postcall Customer Data Table - stores caller and postcall analysis data"""
    __tablename__ = "postcall_cust_data"
 
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PG_UUID(as_uuid=True), ForeignKey("customer_master.customer_id"), nullable=False)
    user_name = Column(Text, nullable=False)
    user_phone = Column(Text, nullable=True)
    user_mail = Column(CITEXT, nullable=True)
    account_status = Column(Text, nullable=True)
    preferred_language = Column(Text, nullable=True)
    preferred_contact_time = Column(Text, nullable=True)
    agent_contact_allowed = Column(Boolean, nullable=True)
    collector_name = Column(Text, nullable=True)
    collector_id = Column(Text, nullable=True)
    billing_address = Column(Text, nullable=True)
    credit_limit = Column(Numeric(18, 2), nullable=True)
    invoice_amount = Column(Numeric(18, 2), nullable=True)
    short_payment = Column(Integer, nullable=True)
    over_payment = Column(Integer, nullable=True)
    call_type = Column(Integer, nullable=True)
    dispute = Column(Numeric(18, 2), nullable=True)
    payment_terms = Column(Text, nullable=True)
    status = Column(Text, nullable=True)
    date = Column(DateTime, nullable=True)
    notes = Column(JSONB, nullable=True)
    audio_recording_enable = Column(Boolean, nullable=True)
    agent_call = Column(Boolean, nullable=True)
    transcript = Column(Boolean, nullable=True)
    call_prompt = Column(Text, nullable=True)
    transcript_address = Column(Text, nullable=True)
    audio_address = Column(Text, nullable=True)
    action_items = Column(JSONB, nullable=True)
    summary = Column(Text, nullable=True)
    categorization = Column(Text, nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
 
    customer = relationship("CustomerMaster")