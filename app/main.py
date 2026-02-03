from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from fastapi.middleware.cors import CORSMiddleware

from core.database import engine, Base
from core.confiq import CORS_ORIGINS

from routes.novotel_routes import n_router
from routes.auth import router as auth_router
from routes.hotels_info_routes import router as hotels_info_router  
from routes.turkey_invoices_routes import router as turkey_invoices_router 
from routes.admin_routes import router as admin_router  
from routes.dashboard_data import router as dashboard_router    
# from routes.employees_routes import router as employees_router 


# --------------------------------------------------
# Logging Configuration
# --------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --------------------------------------------------
# Lifespan (Startup / Shutdown)
# --------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")

    try:
        logger.info("Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(" Database tables created successfully")
    except Exception as e:
        logger.error(f" Database creation failed: {e}")
        raise

    yield

    logger.info("Shutting down application...")
    await engine.dispose()


# --------------------------------------------------
# FastAPI App
# --------------------------------------------------
app = FastAPI(
    title="Hotel Invoice API",
    description="Async FastAPI with JWT Auth & Auto DB Setup",
    version="1.0.0",
    lifespan=lifespan
)


# --------------------------------------------------
# CORS Middleware
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Routers
# --------------------------------------------------
app.include_router(auth_router)
app.include_router(n_router)
app.include_router(hotels_info_router)
app.include_router(turkey_invoices_router)
app.include_router(admin_router)
app.include_router(dashboard_router)

# app.include_router(employees_router)


# --------------------------------------------------
# Root Endpoint
# --------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "Hotel Invoice Management API",
        "version": "1.0.0",
        "status": "Running",
        "features": [
            "JWT Authentication",
            "HttpOnly Refresh Token",
            "Async PostgreSQL",
            "Automatic DB Table Creation",
            "Invoice CRUD",
            "PDF Generation",
            "Search Functionality"
        ]
    }


# --------------------------------------------------
# Run (Local Only)
# --------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
