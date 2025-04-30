from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import generator

app = FastAPI(title="Agent Generator API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(generator.router, prefix="/api", tags=["generator"])

@app.get("/")
async def root():
    return {"message": "Agent Generator API"}
