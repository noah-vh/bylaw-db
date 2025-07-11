#!/usr/bin/env python3
"""
Simple FastAPI server for testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Bylaw Database API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Bylaw Database API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/municipalities")
async def get_municipalities():
    return [
        {
            "id": "1", 
            "name": "Toronto", 
            "province": "Ontario",
            "website_url": "https://www.toronto.ca",
            "scraping_enabled": True,
            "created_at": "2025-01-01T00:00:00Z",
            "metadata": {}
        },
        {
            "id": "2", 
            "name": "Vancouver", 
            "province": "British Columbia",
            "website_url": "https://vancouver.ca",
            "scraping_enabled": True,
            "created_at": "2025-01-01T00:00:00Z",
            "metadata": {}
        },
        {
            "id": "3", 
            "name": "Montreal", 
            "province": "Quebec",
            "website_url": "https://ville.montreal.qc.ca",
            "scraping_enabled": True,
            "created_at": "2025-01-01T00:00:00Z",
            "metadata": {}
        }
    ]

@app.post("/api/municipalities")
async def create_municipality(municipality: dict):
    # In a real implementation, this would save to database
    new_municipality = {
        "id": "4",
        "name": municipality.get("name"),
        "province": municipality.get("province"),
        "website_url": municipality.get("website_url"),
        "scraping_enabled": True,
        "created_at": "2025-01-01T00:00:00Z",
        "metadata": {}
    }
    return new_municipality

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)