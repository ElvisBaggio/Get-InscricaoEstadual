from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
import asyncio

from routes.ie_routes import router as ie_router
from routes.cache_routes import router as cache_router
from utils.logger import app_logger
from utils.config import settings
from utils.database import init_db

app = FastAPI(
    title="CADESP IE API",
    description="API para consulta de Inscrição Estadual no CADESP",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    app_logger.info("Starting CADESP IE API")
    app_logger.info("Initializing FastAPI application")
    app.state.loop = asyncio.get_running_loop()
    
    # Initialize database
    app_logger.info("Initializing database")
    init_db()

@app.on_event("shutdown")
async def shutdown_event():
    app_logger.info("Shutting down CADESP IE API")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    elapsed_time = time.time() - start_time
    
    app_logger.info(
        f"Request: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Client: {request.client.host} - "
        f"Time: {elapsed_time:.2f}s"
    )
    
    return response

# Configure CORS
app_logger.debug("Configuring CORS middleware")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ALLOW_ORIGINS],
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=[settings.CORS_ALLOW_METHODS],
    allow_headers=[settings.CORS_ALLOW_HEADERS],
)

# Include routes
app_logger.debug("Including API routes")
app.include_router(ie_router)
app.include_router(cache_router)

@app.get("/")
async def root():
    app_logger.debug("Health check request received")
    return {
        "message": "CADESP IE API is running",
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    app_logger.info("Starting Uvicorn server")
    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
