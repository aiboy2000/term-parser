from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from pathlib import Path

from term_extractor.api.routes import router as api_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create FastAPI app
app = FastAPI(
    title="Construction Term Extractor API",
    description="API for extracting and searching construction industry terms from documents",
    version="1.0.0"
)

# Add CORS middleware for future web integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1", tags=["terms"])


@app.get("/")
async def root():
    return {
        "message": "Construction Term Extractor API",
        "version": "1.0.0",
        "endpoints": {
            "search": "/api/v1/search",
            "extract": "/api/v1/extract",
            "batch_extract": "/api/v1/extract/batch",
            "database_info": "/api/v1/database/info",
            "list_terms": "/api/v1/terms"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    # Create data directory if not exists
    Path("./data").mkdir(exist_ok=True)
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )