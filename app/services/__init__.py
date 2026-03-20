"""
Query handler service for collections management
Contains business logic for filtering, joining tables, and calculating fields
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from app.models import (
    CallQueue, CustomerMasterData, InvoiceBalanceTable, DunningStage,
    CallOutcome, PromiseToPay, Escalation, Dispute, DocumentCopy,
    PartialPayment, DoubtfulReceivable, CreditRequest, OtherCustomerRequest
)
from app.schemas import QueueItem, QueueListResponse, CaseDetailsResponse, CallOutcomeResponse


class QueryHandlerService:
    """Service for handling collection queue queries"""

    def __init__(self, db: Session):
        self.db = db

    def get_collection_queue(
        self,
        date_param: Optional[date] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        status: Optional[str] = None,
        stage: Optional[str] = None,
        due_date: Optional[date] = None,
        due_from: Optional[date] = None,
        due_to: Optional[date] = None,
        customer_number: Optional[str] = None,
        aging_bucket: Optional[str] = None
    ) -> QueueListResponse:
        """
        Get collection queue with various filtering options
        
        Args:
            date_param: Get data for specific date (default: today)
            from_date: Date range start
            to_date: Date range end
            status: Filter by action status (PromiseToPay, Failed, etc)
            stage: Filter by dunning stage (Call-1, Call-2, etc)
            due_date: Filter by specific due date
            due_from: Due date range start
            due_to: Due date range end
            customer_number: Filter by customer
            aging_bucket: Filter by aging bucket (>60, >90 days)
        """

        # Default to today if no date specified
        query_date = date_param or date.today()

        # Start base query with joins
        query = self.db.query(CallQueue).join(
            CustomerMasterData,
            CallQueue.customer_number == CustomerMasterData.customer_number
        )

        # Apply date filter
        if from_date and to_date:
            query = query.filter(
                and_(
                    CallQueue.queue_date >= from_date,
                    CallQueue.queue_date <= to_date
                )
            )
        elif date_param:
            query = query.filter(CallQueue.queue_date == query_date)

        # Apply status filter
        if status:
            query = query.filter(CallQueue.action_status == status)

        # Apply stage filter
        if stage:
            query = query.filter(CallQueue.dunning_stage == stage)

        # Apply due date filters
        if due_from and due_to:
            # Get invoices with due dates in range
            invoice_query = self.db.query(InvoiceBalanceTable.customer_number).filter(
                and_(
                    InvoiceBalanceTable.due_date >= due_from,
                    InvoiceBalanceTable.due_date <= due_to
                )
            )
            query = query.filter(CallQueue.customer_number.in_(invoice_query))
        elif due_date:
            invoice_query = self.db.query(InvoiceBalanceTable.customer_number).filter(
                InvoiceBalanceTable.due_date == due_date
            )
            query = query.filter(CallQueue.customer_number.in_(invoice_query))

        # Apply customer filter
        if customer_number:
            query = query.filter(CallQueue.customer_number == customer_number)

        # Apply aging bucket filter
        if aging_bucket:
            query = query.filter(CallQueue.aging_bucket_category == aging_bucket)

        # Execute query
        queue_entries = query.all()

        # Build response items
        items = []
        for queue_entry in queue_entries:
            item = self._build_queue_item(queue_entry)
            if item is not None:
                items.append(item)

        return QueueListResponse(
            total_records=len(items),
            records=items
        )

    def get_case_details(self, case_id: str) -> CaseDetailsResponse:
        """
        Get detailed information about a specific case for the detailed UI view.
        """
        # Get queue entry with all related data
        queue_entry = self.db.query(CallQueue).filter(CallQueue.case_id == case_id).first()
        if not queue_entry:
            raise ValueError(f"Case {case_id} not found")

        # Get customer data
        customer = self.db.query(CustomerMasterData).filter(CustomerMasterData.customer_number == queue_entry.customer_number).first()
        if not customer:
            raise ValueError(f"Customer not found for case {case_id}")

        # Get all invoices for this case
        invoice_numbers = queue_entry.invoice_nos or []
        outstanding_balance, due_date = self._calculate_outstanding_balance(invoice_numbers, queue_entry.multiple_invoice)

        # Get workflow steps from DunningStage (example: static config, or filter by case_id if dynamic)
        dunning_stages = self.db.query(DunningStage).order_by(DunningStage.stage_day).all()
        workflow_steps = [
            {
                "day": stage.stage_day,
                "label": stage.stage_label,
                "date": stage.stage_date.strftime("%Y-%m-%d") if stage.stage_date else None,
                "active": bool(stage.stage_active)
            }
            for stage in dunning_stages
        ]

        # Get call outcomes (history)
        call_outcomes = self.db.query(CallOutcome).filter(CallOutcome.case_id == case_id).order_by(CallOutcome.attempt_number).all()
        # Use the latest call outcome for transcript/summary/recording (or adjust as needed)
        latest_call = call_outcomes[-1] if call_outcomes else None

        # Parse full_transcript (assume JSON string or list in DB)
        import json
        full_transcript = None
        if latest_call and latest_call.full_transcript:
            try:
                full_transcript = json.loads(latest_call.full_transcript)
            except Exception:
                full_transcript = latest_call.full_transcript  # fallback as string

        call_summary = latest_call.call_summary if latest_call and latest_call.call_summary else []
        call_recording = latest_call.call_recording_url if latest_call and latest_call.call_recording_url else None

        # Aggregate actions for all calls in this case
        actions = self._get_all_actions_for_case(case_id, call_outcomes)

        return CaseDetailsResponse(
            case_id=str(queue_entry.case_id),
            customer_number=str(customer.customer_number),
            phone=customer.phone_number,
            email=customer.email_address,
            region=self._get_region_from_address(customer.billing_address),
            invoice_numbers=invoice_numbers,
            due_date=due_date,
            outstanding_balance=outstanding_balance,
            workflow_steps=workflow_steps,
            full_transcript=full_transcript,
            call_summary=call_summary,
            actions=actions,
            call_recording=call_recording
        )

    def get_call_details(self, call_id: str) -> CallOutcomeResponse:
        """
        Get detailed information about a specific call
        
        Args:
            call_id: Unique call identifier
        """

        # Get call outcome
        call_outcome = self.db.query(CallOutcome).filter(
            CallOutcome.call_id == call_id
        ).first()

        if not call_outcome:
            raise ValueError(f"Call {call_id} not found")

        # Get customer data
        customer = self.db.query(CustomerMasterData).filter(
            CustomerMasterData.customer_number == call_outcome.customer_number
        ).first()

        if not customer:
            raise ValueError(f"Customer not found for call {call_id}")

        # Get all actions for this call
        actions = self._get_actions_for_call(call_id)

        return CallOutcomeResponse(
            call_id=call_outcome.call_id,
            case_id=str(call_outcome.case_id) if call_outcome.case_id else "",
            customer_number=str(customer.customer_number),
            customer_name=customer.customer_name,
            phone=customer.phone_number,
            email=customer.email_address,
            invoice_numbers=call_outcome.invoice_numbers or [],
            attempt_number=call_outcome.attempt_number,
            call_start_at=call_outcome.call_start_at,
            call_end_at=call_outcome.call_end_at,
            call_status=call_outcome.call_status,
            voice_mail=call_outcome.voice_mail,
            full_transcript=call_outcome.full_transcript,
            call_summary=call_outcome.call_summary,
            call_recording_url=call_outcome.call_recording_url,
            actions_taken=actions
        )

    # ============= Private Helper Methods =============

    def _build_queue_item(self, queue_entry: CallQueue) -> Optional[QueueItem]:
        """Build a queue item from queue entry with all calculations"""

        # Get customer data
        customer = self.db.query(CustomerMasterData).filter(
            CustomerMasterData.customer_number == queue_entry.customer_number
        ).first()
        
        if not customer:
            return None

        # Calculate outstanding balance and due date
        outstanding_balance, due_date = self._calculate_outstanding_balance(
            queue_entry.invoice_nos,
            queue_entry.multiple_invoice
        )

        # Calculate age
        age = self._calculate_age(due_date) if due_date else None

        return QueueItem(
            case_id=str(queue_entry.case_id),
            customer_number=str(customer.customer_number),
            customer_name=customer.customer_name,
            phone=customer.phone_number,
            email=customer.email_address,
            region=self._get_region_from_address(customer.billing_address),
            invoice_nos=queue_entry.invoice_nos or [],
            outstanding_balance=outstanding_balance,
            due_date=due_date,
            age=age,
            action_status=queue_entry.action_status,
            dunning_stage=queue_entry.dunning_stage,
            time_zone=customer.time_zone,
            multiple_invoice=queue_entry.multiple_invoice,
            aging_bucket_category=queue_entry.aging_bucket_category
        )

    def _calculate_outstanding_balance(
        self,
        invoice_nos: Optional[List[str]],
        multiple_invoice: bool
    ) -> tuple[Decimal, Optional[date]]:
        """
        Calculate outstanding balance based on invoices
        
        Returns:
            Tuple of (outstanding_balance, due_date)
        """

        if not invoice_nos:
            return Decimal(0), None

        # Convert invoice_nos to list if it's a string or other type
        if isinstance(invoice_nos, str):
            invoice_list = [invoice_nos]
        else:
            invoice_list = list(invoice_nos) if invoice_nos else []

        if not invoice_list:
            return Decimal(0), None

        # Query invoices by document_number (the invoice numbers stored in queue)
        invoices = self.db.query(InvoiceBalanceTable).filter(
            InvoiceBalanceTable.document_number.in_(invoice_list)
        ).all()

        if not invoices:
            return Decimal(0), None

        if not multiple_invoice:
            # Single invoice: get balance from that invoice
            invoice = invoices[0]
            return invoice.outstanding_balance, invoice.due_date
        else:
            # Multiple invoices: sum all balances and return list of ages
            total_balance = sum(
                (inv.outstanding_balance or Decimal(0)) for inv in invoices
            )
            # Use the earliest due date for age calculation
            due_dates = [inv.due_date for inv in invoices if inv.due_date]
            earliest_due_date = min(due_dates) if due_dates else None
            return total_balance, earliest_due_date

    def _calculate_age(self, due_date: Optional[date]) -> Optional[int]:
        """
        Calculate age in days from due date to today
        
        Returns:
            Number of days (negative if not yet due, positive if overdue)
        """

        if not due_date:
            return None

        today = date.today()
        age_delta = today - due_date
        return age_delta.days

    def _get_region_from_address(self, billing_address: Optional[str]) -> Optional[str]:
        """
        Extract region from billing address (simple implementation)
        In real scenario, might need more sophisticated parsing
        """

        if not billing_address:
            return None

        # Simple implementation - could be enhanced
        parts = billing_address.split(',')
        if len(parts) >= 2:
            return parts[-2].strip()
        return billing_address

    def _get_actions_for_call(self, call_id: str) -> List[Dict[str, Any]]:
        """Get all actions taken for a specific call"""

        actions = []

        # Get PromiseToPay actions
        ptp_actions = self.db.query(PromiseToPay).filter(
            PromiseToPay.call_id == call_id
        ).all()
        for ptp in ptp_actions:
            actions.append({
                "action_type": "PromiseToPay",
                "action_id": str(ptp.action_id),
                "created_at": None,
                "details": {
                    "promised_amount": float(ptp.promised_amount) if ptp.promised_amount else None,
                    "promised_date": ptp.promised_date.isoformat() if ptp.promised_date else None,
                    "payment_method": ptp.payment_method,
                    "reference_number": ptp.reference_number
                }
            })

        # Get Escalation actions
        escalations = self.db.query(Escalation).filter(
            Escalation.call_id == call_id
        ).all()
        for esc in escalations:
            actions.append({
                "action_type": "Escalation",
                "action_id": str(esc.action_id),
                "created_at": None,
                "details": {
                    "escalation_level": esc.escalation_level,
                    "escalated_to_role": esc.escalated_to_role,
                    "reason": esc.reason
                }
            })

        # Get Dispute actions
        disputes = self.db.query(Dispute).filter(
            Dispute.call_id == call_id
        ).all()
        for disp in disputes:
            actions.append({
                "action_type": "Dispute",
                "action_id": str(disp.action_id),
                "created_at": None,
                "details": {
                    "dispute_category": disp.dispute_category,
                    "description": disp.description,
                    "disputed_amount": float(disp.disputed_amount) if disp.disputed_amount else None
                }
            })

        # Get DocumentCopy actions
        doc_copies = self.db.query(DocumentCopy).filter(
            DocumentCopy.call_id == call_id
        ).all()
        for doc in doc_copies:
            actions.append({
                "action_type": "DocumentCopy",
                "action_id": str(doc.action_id),
                "created_at": doc.sent_at,
                "details": {
                    "document_type": doc.document_type,
                    "delivery_channel": doc.delivery_channel,
                    "delivery_status": doc.delivery_status
                }
            })

        # Get PartialPayment actions
        partial_payments = self.db.query(PartialPayment).filter(
            PartialPayment.call_id == call_id
        ).all()
        for pp in partial_payments:
            actions.append({
                "action_type": "PartialPayment",
                "action_id": str(pp.action_id),
                "created_at": pp.payment_date,
                "details": {
                    "amount": float(pp.amount),
                    "payment_method": pp.payment_method,
                    "reference_number": pp.reference_number
                }
            })

        return actions

    def _get_all_actions_for_case(
        self,
        case_id: str,
        call_outcomes: List[CallOutcome]
    ) -> List[Dict[str, Any]]:
        """Get all actions for all calls in a case"""

        all_actions = []
        for call in call_outcomes:
            actions = self._get_actions_for_call(call.call_id)
            all_actions.extend(actions)

        return all_actions
