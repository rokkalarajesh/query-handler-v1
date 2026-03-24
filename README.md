# Collections Query Handler API

A comprehensive FastAPI-based query handler for managing collection queue, cases, and calls with PostgreSQL backend.

## Overview

This API provides endpoints to query and manage collection activities with support for:
- Collection queue filtering by date, status, stage, and due date ranges
- Case details retrieval with calculated fields (outstanding balance, age)
- Call details and outcomes tracking
- Action tracking (Promise to Pay, Escalation, Dispute, etc.)

## Architecture

```
app/
├── database.py           # PostgreSQL connection and session management
├── main.py              # FastAPI application setup
├── routes.py            # API endpoints
├── models/
│   └── __init__.py      # SQLAlchemy ORM models
├── schemas/
│   └── __init__.py      # Pydantic request/response schemas
└── services/
    └── __init__.py      # Business logic and query handling
```

## Database Schema

### Tables

1. **customer_master_data** - Customer information
2. **invoice_balance_table** - Invoice and transaction data
3. **call_queue** - Collection queue entries
4. **dunning_stage** - Dunning stage tracking
5. **call_outcome** - Call results and details
6. **Action Tables:**
   - promise_to_pay
   - escalation
   - dispute
   - document_copy
   - partial_payment
   - doubtful_receivable
   - credit_request
   - other_customer_request

## Setup Instructions

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   cd query-handler
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   
   # Edit .env with your database credentials
   ```

   Example .env:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/collections_db
   API_HOST=0.0.0.0
   API_PORT=8000
   API_DEBUG=True
   LOG_LEVEL=INFO
   ```

5. **Create PostgreSQL database**
   ```sql
   CREATE DATABASE collections_db;
   ```

6. **Run the application**
   ```bash
   # Development mode with auto-reload
   python -m uvicorn app.main:app --reload
   
   # Production mode
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

7. **Access API Documentation**
   - Swagger UI: http://localhost:8000/api/docs
   - ReDoc: http://localhost:8000/api/redoc
   - OpenAPI JSON: http://localhost:8000/api/openapi.json

## API Endpoints

### 1. Get Collection Queue

**Endpoint:** `GET /collections/queue`

**Query Parameters:**
- `date` (optional): Specific date (default: today) - Format: YYYY-MM-DD
- `from` (optional): Date range start - Format: YYYY-MM-DD
- `to` (optional): Date range end - Format: YYYY-MM-DD
- `status` (optional): Filter by action status (e.g., PromiseToPay, Failed)
- `stage` (optional): Filter by dunning stage (e.g., Call-1, Call-2)
- `due_date` (optional): Filter by specific due date - Format: YYYY-MM-DD
- `due_from` (optional): Due date range start - Format: YYYY-MM-DD
- `due_to` (optional): Due date range end - Format: YYYY-MM-DD
- `customer_number` (optional): Filter by customer UUID
- `aging_bucket` (optional): Filter by aging bucket (e.g., >60, >90)

**Examples:**

```bash
# Get today's queue
curl "http://localhost:8000/collections/queue"

# Get queue for specific date
curl "http://localhost:8000/collections/queue?date=2026-03-16"

# Get queue for date range
curl "http://localhost:8000/collections/queue?from=2026-03-01&to=2026-03-16"

# Filter by status and stage
curl "http://localhost:8000/collections/queue?status=PromiseToPay&stage=Call-1"

# Filter by due date range
curl "http://localhost:8000/collections/queue?due_from=2026-03-01&due_to=2026-03-16"
```

**Response:**
```json
{
  "total_records": 5,
  "records": [
    {
      "case_id": "123e4567-e89b-12d3-a456-426614174000",
      "customer_number": "CUST001",
      "customer_name": "David Miller",
      "phone": "040-213-123",
      "email": "david@example.com",
      "region": "Latin America",
      "invoice_nos": ["INV001", "INV002"],
      "outstanding_balance": 4000.75,
      "due_date": "2025-08-28",
      "age": 30,
      "action_status": "PromiseToPay",
      "dunning_stage": "Call-1",
      "time_zone": "IST",
      "multiple_invoice": false,
      "aging_bucket_category": ">60"
    }
  ]
}
```

### 2. Get Case Details

**Endpoint:** `GET /collections/case/{case_id}/details`

**Path Parameters:**
- `case_id`: Unique case identifier (UUID)

**Example:**
```bash
curl "http://localhost:8000/collections/case/123e4567-e89b-12d3-a456-426614174000/details"
```

**Response:**
```json
{
  "case_id": "123e4567-e89b-12d3-a456-426614174000",
  "customer_number": "CUST001",
  "customer_name": "David Miller",
  "phone": "040-213-123",
  "email": "david@example.com",
  "region": "Latin America",
  "invoice_nos": ["INV001", "INV002"],
  "outstanding_balance": 4000.75,
  "due_date": "2025-08-28",
  "age": 30,
  "action_status": "PromiseToPay",
  "dunning_stage": "Call-1",
  "time_zone": "IST",
  "queue_date": "2026-03-17",
  "stage_date": "2026-08-31",
  "stage_active": true,
  "multiple_invoice": false,
  "aging_bucket_category": ">60",
  "call_history": [
    {
      "call_id": "CALL001",
      "attempt_number": 1,
      "call_start_at": "2026-03-17T09:20:32Z",
      "call_end_at": "2026-03-17T09:32:10Z",
      "call_status": "Success",
      "voice_mail": false,
      "call_summary": ["Customer promised payment", "Invoice INV001 discussed"],
      "call_recording_url": "https://recordings.example.com/call001.wav"
    }
  ],
  "actions": [
    {
      "action_type": "PromiseToPay",
      "action_id": "ACT001",
      "created_at": null,
      "details": {
        "promised_amount": 2000.00,
        "promised_date": "2026-04-15",
        "payment_method": "BankTransfer",
        "reference_number": "REF123"
      }
    }
  ]
}
```

### 3. Get Call Details

**Endpoint:** `GET /collections/call/{call_id}`

**Path Parameters:**
- `call_id`: Unique call identifier (string)

**Example:**
```bash
curl "http://localhost:8000/collections/call/CALL001"
```

**Response:**
```json
{
  "call_id": "CALL001",
  "case_id": "123e4567-e89b-12d3-a456-426614174000",
  "customer_number": "CUST001",
  "customer_name": "David Miller",
  "phone": "040-213-123",
  "email": "david@example.com",
  "invoice_numbers": ["INV001", "INV002"],
  "attempt_number": 1,
  "call_start_at": "2026-03-17T09:20:32Z",
  "call_end_at": "2026-03-17T09:32:10Z",
  "call_status": "Success",
  "voice_mail": false,
  "full_transcript": "Agent: Hello, this is about invoice INV001...",
  "call_summary": ["Customer promised payment", "Invoice discussed"],
  "call_recording_url": "https://recordings.example.com/call001.wav",
  "actions_taken": [
    {
      "action_type": "PromiseToPay",
      "action_id": "ACT001",
      "created_at": null,
      "details": {
        "promised_amount": 2000.00,
        "promised_date": "2026-04-15",
        "payment_method": "BankTransfer",
        "reference_number": "REF123"
      }
    }
  ]
}
```
Invoices API
----------------
API Endpoint
GET /invoices/
http://localhost:8000/invoices/

Description
Returns invoice records linked to customers.


Sample Invoice Record

{
  "document_number": "INV-1001",
  "original_amount": 15000,
  "open_ptp": true,
  "issued_credits": 0,
  "outstanding_balance": 5000,
  "open_ptp_date": "2026-02-28T00:00:00",
  "applied_payment_date": null,
  "customer_id": "2eae0fe9-e903-4fe9-9655-d5d8497b6d09",
  "document_status": "OVERDUE",
  "broken_ptp_flag": false,
  "applied_payment_amount": null,
  "due_date": "2026-02-20T00:00:00",
  "broken_ptp_amount": null,
  "days_past_due": 20,
  "broken_ptp_date": null,
  "transaction_id": "ddd85b87-8672-4561-bf77-4025e7826087",
  "purchase_order_number": "PO-77",
  "open_dispute": false,
  "document_type": "INVOICE",
  "order_date": "2026-01-15T00:00:00",
  "closed_dispute": false,
  "document_date": "2026-02-01T00:00:00",
  "delivery_date": "2026-01-20T00:00:00",
  "closed_dispute_status": null
}

-------------
Call Handle API
API Endpoint
POST /create_collection_case_call_handle/
http://127.0.0.1:8000/docs#/default/create_collection_case_call_handle__post

Purpose
Creates a call-handling case combining:
✅ customer details
✅ one or more invoices
✅ call activity, notes, call type
✅ DNC (Do Not Contact) settings
✅ call failed reasons
✅ timestamps
✅ calling window
✅ consent & voice mail info

Sample Request Payload

{
  "customer_id": "2eae0fe9-e903-4fe9-9655-d5d8497b6d09",
  "uniqid": "string",
  "invoice_numbers": [
    {
      "inovice_n": "INV-1001",
      "outstanding_balance": 0,
      "overdue_status": "string",
      "due_date": "2026-03-13T08:14:12.030Z",
      "days_past_due": 0,
      "purchase_order_num": "string",
      "order_date": "2026-03-13T08:14:12.030Z",
      "open_ptp": true,
      "open_ptp_date": "2026-03-13T08:14:12.030Z",
      "broken_ptp_flg": true,
      "broken_ptp_amount": 0,
      "broken_ptp_date": "2026-03-13T08:14:12.030Z",
      "open_dispute": true,
      "closed_dispute_status": "string",
      "isseues_credits": 0
    }
  ],
  "multiple_invoice": false,
  "aging_bucket": "string",
  "priority": 0,
  "due_at": "2026-03-13T08:14:12.030Z",
  "call_notes": [
    {
      "author": "string",
      "note": "string",
      "created_at": "2026-03-13T08:14:12.030Z"
    }
  ],
  "call_type": "1",
  "activity_status": true,
  "activity_empty_reason": "string",
  "dnc_status": true,
  "dnc_reason_yes": "customer not willing",
  "record_consent": true,
  "customer_name": "string",
  "billing_address": "string",
  "contact_name": "string",
  "phone_number": "string",
  "email_address": "string",
  "calling_window": ["2026-03-12T09:00:00", "2026-03-12T17:30:00"],
  "time_zone": "America/New_York",
  "Call_failed": {
    "status": "string",
    "errors": ["string"],
    "summary": {
      "total_errors": 0,
      "error_categories": ["string"]
    }
  },
  "call_data": {
    "attempt_number": 0,
    "call_start_at": "2026-03-13T08:14:12.030Z",
    "call_end_at": "2026-03-13T08:14:12.030Z",
    "call_status": "string",
    "Voice mail": true,
    "Transcript": {},
    "Actions": {}
  }
}

Sample API Response (Call Handle Output):
Case ID format = tenant_id + customer_id + unique_id


{
  "case_id": "tnt-20-002-2eae0fe9-e903-4fe9-9655-d5d8497b6d09-a2b190ea2e8c4511ac04a6d78b8876f4",
  "customer_id": "2eae0fe9-e903-4fe9-9655-d5d8497b6d09",
  "customer_name": "Gappraj Pvt Ltd",
  "billing_address": "Secunderabad, Paradise",
  "contact_name": "Raj",
  "phone_number": "84312329123",
  "email_address": "raj@gappraj.com",
  "preferred_language": "English",
  "preferred_contact_hours": [
    "2026-03-12T09:00:00",
    "2026-03-12T17:30:00"
  ],
  "time_zone": "America/New_York",
  "attempt_number": 0,
  "multiple_invoice": false,
  "call_data": {
    "Actions": {},
    "Transcript": {},
    "Voice mail": true,
    "call_end_at": "2026-03-13T08:14:12.030Z",
    "call_status": "string",
    "call_start_at": "2026-03-13T08:14:12.030Z",
    "attempt_number": 0
  },
  "call_failed": {
    "errors": ["string"],
    "status": "string",
    "summary": {
      "total_errors": 0,
      "error_categories": ["string"]
    }
  }
}


--------------------
Call Workflow API
API Endpoint
POST /call-workflow
http://localhost:8000/call-workflow

Purpose
Takes the stored case and:
✅ Merges full customer data
✅ Merges all invoice data
✅ Merges call handler details
✅ Increments attempt_number automatically
✅ Max retry attempts = 3

sample response 
{
  "case_id": "tnt-20-002-2eae0fe9-e903-4fe9-9655-d5d8497b6d09-136cc762595b4e7e9b56b661cc4f929d",
  "attempt_number": 3,
  "customer_info": {
    "customer_id": "2eae0fe9-e903-4fe9-9655-d5d8497b6d09",
    "customer_name": "Gappraj Pvt Ltd",
    "billing_address": "Secunderabad, Paradise",
    "contact_name": "Raj",
    "phone_number": "84312329123",
    "email_address": "raj@gappraj.com",
    "preferred_language": "English",
    "time_zone": "string"
  },
  "invoice_info": [
    {
      "document_number": "INV-1001",
      "outstanding_balance": 5000,
      "due_date": "2026-02-20T00:00:00",
      "days_past_due": 20,
      "open_ptp": true,
      "open_dispute": false
    },
    {
      "document_number": "INV-1002",
      "outstanding_balance": 7500,
      "due_date": "2026-03-25T00:00:00",
      "days_past_due": 0,
      "open_ptp": false,
      "open_dispute": false
    },
    {
      "document_number": "INV-1003",
      "outstanding_balance": 12000,
      "due_date": "2026-01-30T00:00:00",
      "days_past_due": 40,
      "open_ptp": true,
      "open_dispute": false
    }
  ],
  "call_handler": {
    "Transcript": {},
    "Voice mail": true,
    "call_end_at": "2026-03-13T07:16:03.288Z",
    "call_status": "string",
    "call_start_at": "2026-03-13T07:16:03.288Z",
    "attempt_number": 3
  },
  "call_failed": {
    "errors": ["string"],
    "status": "failed",
    "summary": {
      "total_errors": 0,
      "error_categories": ["string"]
    }
  }
}
--------------




### 4. Health Check

**Endpoint:** `GET /collections/health`

**Example:**
```bash
curl "http://localhost:8000/collections/health"
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "Collections Query Handler API"
}
```

## Calculated Fields

### Outstanding Balance

The API automatically calculates outstanding balance based on invoice configuration:

**For Single Invoice (multiple_invoice = false):**
- Gets outstanding balance directly from the invoice record

**For Multiple Invoices (multiple_invoice = true):**
- Sums all outstanding balances across all invoices
- Uses earliest due date for age calculation

### Age Calculation

Age is calculated in days from the due date to today:
- Negative value: Invoice not yet due
- Zero: Due today
- Positive value: Days overdue

**Formula:** `Age = Today's Date - Due Date`

## Data Flow

1. **Queue Request** → Filters call_queue table → Joins with customer_master_data and invoice_balance_table → Returns calculated queue items

2. **Case Details Request** → Retrieves call_queue entry → Gets related customer, invoices, calls, and actions → Calculates balance and age → Returns comprehensive case details

3. **Call Details Request** → Retrieves call_outcome → Gets customer info and all related actions → Returns call details with actions

## Error Handling

The API implements comprehensive error handling:

| Status Code | Meaning |
|---|---|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Case or Call not found |
| 500 | Internal Server Error |

**Error Response Format:**
```json
{
  "detail": "Error message describing the issue"
}
```

## Performance Considerations

1. **Database Indexing**: Consider adding indexes on:
   - `call_queue.queue_date`
   - `call_queue.action_status`
   - `call_queue.dunning_stage`
   - `invoice_balance_table.due_date`
   - `customer_master_data.customer_number`

2. **Query Optimization**: Complex queries join multiple tables; consider:
   - Connection pooling (implemented via SQLAlchemy)
   - Query result caching for frequently accessed data
   - Pagination for large result sets (can be added)

3. **Scaling**: For high-volume scenarios:
   - Use read replicas for queries
   - Implement caching layer (Redis)
   - Add pagination to list endpoints

## Testing

Run tests using pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_routes.py -v
```

## Development

### Project Structure Rationale

- **Models**: SQLAlchemy ORM definitions for all tables
- **Schemas**: Pydantic models for request/response validation and documentation
- **Services**: Business logic and query construction
- **Routes**: FastAPI endpoint definitions
- **Database**: Connection management and session handling

### Adding New Endpoints

1. Add Pydantic schema in `app/schemas/__init__.py`
2. Add query method in `app/services/__init__.py`
3. Add route in `app/routes.py`
4. Document with docstrings and examples

## Production Deployment

### Environment Variables

Create `.env` for production with:
```
DATABASE_URL=postgresql://prod_user:prod_pass@prod_host:5432/collections_db
API_DEBUG=False
LOG_LEVEL=WARNING
ALLOWED_ORIGINS=https://your-domain.com
```

### Running with Gunicorn

```bash
pip install gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t collections-api .
docker run -p 8000:8000 --env-file .env collections-api
```

## Security Considerations

1. **Authentication**: Add authentication middleware (JWT, OAuth2)
2. **Authorization**: Implement role-based access control
3. **Data Validation**: Pydantic validates all inputs
4. **SQL Injection**: SQLAlchemy ORM prevents SQL injection
5. **CORS**: Configure allowed origins in production
6. **Rate Limiting**: Add rate limiting middleware
7. **HTTPS**: Use HTTPS in production

## Troubleshooting

### Database Connection Issues

```python
# Test connection
from app.database import engine
with engine.connect() as conn:
    result = conn.execute("SELECT 1")
    print(result.fetchone())
```

### Missing Tables

Tables are created automatically on startup. If not created:

```python
from app.database import engine, Base
Base.metadata.create_all(bind=engine)
```

### Port Already in Use

```bash
# Find and kill process
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Linux/Mac
```

## Support and Contributions

For issues, questions, or contributions, please refer to your internal development guidelines.

## License

Internal Use Only - Collections Management System API
