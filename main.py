from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
import asyncio

from routes.ie_routes import router as ie_router
from utils.logger import app_logger

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
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routes
app_logger.debug("Including API routes")
app.include_router(ie_router)

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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
