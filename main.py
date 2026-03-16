from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import connect_db, close_db
from routes.auth import router as auth_router
from routes.drug_info import router as drug_info_router
from routes.predictions import router as predictions_router
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="AI Drug Discovery Platform API",
    description="Deep Learning & Bioinformatics API for drug discovery, toxicity prediction, and molecular screening",
    version="1.0.0",
    lifespan=lifespan
)

# CORS – allow frontend on any origin in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(drug_info_router)
app.include_router(predictions_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "AI Drug Discovery Platform API is running 🧬",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "healthy"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "drug-discovery-ai"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
