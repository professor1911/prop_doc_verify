from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from typing import Dict, Any
import json
from datetime import datetime

from .vlm_processor import VLMProcessor
from .llm_reasoner import LLMReasoner
from .models.document_schemas import DocumentAnalysis
from .utils.file_handler import FileHandler

app = FastAPI(title="Property Document Verifier", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
vlm_processor = VLMProcessor()
llm_reasoner = LLMReasoner()
file_handler = FileHandler()

@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    await vlm_processor.initialize()
    await llm_reasoner.initialize()
    os.makedirs("uploads", exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Property Document Verifier API", "status": "running"}

@app.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = "Rent Agreement"
):
    """
    Upload and process property document
    """
    try:
        # Validate file type
        if not file_handler.is_valid_file(file.filename):
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Save uploaded file
        file_path = await file_handler.save_file(file, document_type)
        
        # Process with VLM
        extracted_data = await vlm_processor.extract_document_data(file_path, document_type)
        
        # Analyze with LLM
        analysis_result = await llm_reasoner.analyze_document(extracted_data, document_type)
        
        # Create response
        response = {
            "documentType": document_type,
            "filename": file.filename,
            "uploadTime": datetime.now().isoformat(),
            "analysis": analysis_result,
            "status": "success"
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.get("/document-types")
async def get_document_types():
    """Get supported document types and their file formats"""
    return {
        "Rent Agreement": [".pdf", ".jpg", ".png"],
        "Title Deed": [".pdf", ".jpg", ".png"],
        "NOC": [".pdf", ".jpg", ".png"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "vlm_status": vlm_processor.is_ready(),
        "llm_status": llm_reasoner.is_ready()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
