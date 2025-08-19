from fastapi import FastAPI
from app.api.endpoints import router as api_router
from app.services.vector_db import VectorDB
from app.services.embedding import EmbeddingService
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="VectorDB API", description="API for Qdrant VectorDB")

# Initialize services
vector_db = VectorDB()
embedding_service = EmbeddingService()

# Include routers
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    # Initialize services
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)