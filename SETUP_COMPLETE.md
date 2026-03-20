# Collections Query Handler API

Fast, production-ready API for managing collection queues, cases, and calls.

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Virtual environment (recommended)

### Installation

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

### Run the API

```bash
python -m uvicorn app.main:app --reload --port 8000
```

API will be available at: **http://localhost:8000**

## API Endpoints

### Collections Queue
- `GET /collections/queue` - Get collection queue
  - Query Parameters: `action_status`, `stage`, `customer_number`, `aging_bucket`, date filters

### Case Details
- `GET /collections/case/{case_id}/details` - Get case details with all related information

### Call Details
- `GET /collections/call/{call_id}` - Get call outcome and actions

### Health Check
- `GET /collections/health` - API health status

### Documentation
- `GET /api/docs` - Interactive Swagger UI
- `GET /api/redoc` - ReDoc documentation

## Sample Data

**Database includes:**
- 3 Customers
- 5 Invoices ($4000+)
- 3 Queue Entries (PromiseToPay status)
- 3 Call Outcomes
- Promise to pay actions

## Database Schema

13 tables with relationships:
- customer_master_data
- invoice_balance_table
- call_queue
- call_outcome
- dunning_stage
- promise_to_pay
- escalation
- dispute
- document_copy
- partial_payment
- doubtful_receivable
- credit_request
- other_customer_request

## Project Structure

```
app/
├── main.py           # FastAPI application
├── database.py       # Database configuration
├── routes.py         # API endpoints
├── models/           # SQLAlchemy ORM models
├── schemas/          # Pydantic request/response models
└── services/         # Business logic

requirements.txt      # Dependencies
.env                  # Environment variables
Dockerfile            # Docker configuration
```

## Technology Stack

- **Framework:** FastAPI
- **Server:** Uvicorn
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Validation:** Pydantic

## Testing

```bash
# Test an endpoint
curl http://localhost:8000/collections/queue

# With filters
curl "http://localhost:8000/collections/queue?action_status=PromiseToPay"
```

## Production Deployment

Ready for deployment with:
- Docker containerization (Dockerfile included)
- Proper error handling
- Database connection pooling
- Async/await patterns
- CORS middleware
- Comprehensive validation

## Environment Variables

```
DATABASE_URL=postgresql://user:password@localhost:5432/collections_db
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=False
LOG_LEVEL=INFO
ALLOWED_ORIGINS=*
```

## Notes

- Database is pre-populated with sample data
- All setup and initialization is complete
- Ready for immediate use and testing
