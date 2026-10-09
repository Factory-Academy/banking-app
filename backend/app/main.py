from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import engine, Base
from app.exceptions import TransactionNotFoundError
from app.routes import transactions_router, stats_router
from app.config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, debug=settings.debug)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transactions_router)
app.include_router(stats_router)


@app.exception_handler(TransactionNotFoundError)
def transaction_not_found_exception_handler(
    request: Request, exc: TransactionNotFoundError
):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.get("/")
def root():
    return {"message": "Transaction Monitoring System API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
