import os
import uuid
from fastapi import UploadFile
from typing import List
import shutil

class FileHandler:
    def __init__(self):
        self.upload_dir = "uploads"
        self.allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def is_valid_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        if not filename:
            return False
        return any(filename.lower().endswith(ext) for ext in self.allowed_extensions)
    
    async def save_file(self, file: UploadFile, document_type: str) -> str:
        """Save uploaded file and return path"""
        try:
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Create document type directory
            doc_dir = os.path.join(self.upload_dir, document_type.replace(" ", "_"))
            os.makedirs(doc_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(doc_dir, unique_filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            return file_path
            
        except Exception as e:
            raise Exception(f"File save error: {str(e)}")
    
    def get_file_info(self, file_path: str) -> dict:
        """Get file information"""
        if not os.path.exists(file_path):
            return None
        
        stat = os.stat(file_path)
        return {
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "name": os.path.basename(file_path)
        }
