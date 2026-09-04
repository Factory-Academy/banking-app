from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routes import transactions_router, stats_router
from app.config import settings
from app.events import event_bus, register_default_subscribers

# Create database tables
Base.metadata.create_all(bind=engine)

# Attach the built-in audit-logging subscribers to the shared event bus.
register_default_subscribers(event_bus)

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


@app.get("/")
def root():
    return {"message": "Transaction Monitoring System API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
