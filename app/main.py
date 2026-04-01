"""
Main FastAPI application for Collections Query Handler
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from app.database import engine, Base
from app.routes.routes import router as main_router
from app.routes.call_handle import router as call_handle_router
from app.routes.agent_workflow import router as agent_workflow_router
from app.models import (
    CustomerMasterData, InvoiceBalanceTable, CallQueue, DunningStage,
    CallOutcome, PromiseToPay, Escalation, Dispute, DocumentCopy,
    PartialPayment, DoubtfulReceivable, CreditRequest, OtherCustomerRequest
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle
    """
    # Startup
    logger.info("Starting Collections Query Handler API")
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Collections Query Handler API")


# Create FastAPI app
app = FastAPI(
    title="Collections Query Handler API",
    description="API for querying and managing collection queue, cases, and calls",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(main_router)
app.include_router(call_handle_router)
app.include_router(agent_workflow_router)


# Root endpoint
@app.get("/", tags=["root"])
def read_root():
    """
    Root endpoint - API information
    """
    return {
        "service": "Collections Query Handler API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/collections/health"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
