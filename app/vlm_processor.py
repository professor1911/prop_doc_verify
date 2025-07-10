import torch
from transformers import LayoutLMv3Processor, LayoutLMv3ForTokenClassification
from PIL import Image
import pdf2image
import pytesseract
import cv2
import numpy as np
from typing import Dict, List, Any
import re
import asyncio

class VLMProcessor:
    def __init__(self):
        self.processor = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.ready = False
    
    async def initialize(self):
        """Initialize LayoutLMv3 model"""
        try:
            self.processor = LayoutLMv3Processor.from_pretrained("microsoft/layoutlmv3-base")
            self.model = LayoutLMv3ForTokenClassification.from_pretrained("microsoft/layoutlmv3-base")
            self.model.to(self.device)
            self.ready = True
            print("VLM Processor initialized successfully")
        except Exception as e:
            print(f"Error initializing VLM: {e}")
            self.ready = False
    
    def is_ready(self) -> bool:
        return self.ready
    
    async def extract_document_data(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """Extract structured data from document"""
        try:
            # Convert PDF to image if needed
            if file_path.lower().endswith('.pdf'):
                images = pdf2image.convert_from_path(file_path)
                image = images[0]  # Process first page
            else:
                image = Image.open(file_path)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(image)
            
            # Extract layout information
            layout_data = self._extract_layout_features(image)
            
            # Process with LayoutLMv3
            structured_data = await self._process_with_layoutlm(image, text)
            
            # Extract document-specific fields
            extracted_fields = self._extract_document_fields(text, document_type)
            
            return {
                "raw_text": text,
                "layout_data": layout_data,
                "structured_data": structured_data,
                "extracted_fields": extracted_fields,
                "document_type": document_type
            }
            
        except Exception as e:
            raise Exception(f"VLM processing error: {str(e)}")
    
    def _extract_layout_features(self, image: Image.Image) -> Dict[str, Any]:
        """Extract layout features from image"""
        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Detect signatures (simple contour detection)
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        signature_detected = len([c for c in contours if cv2.contourArea(c) > 500]) > 0
        
        # Detect stamps (color detection for red/blue)
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        red_mask = cv2.inRange(hsv, (0, 50, 50), (10, 255, 255))
        blue_mask = cv2.inRange(hsv, (100, 50, 50), (130, 255, 255))
        
        stamp_detected = cv2.countNonZero(red_mask) > 1000 or cv2.countNonZero(blue_mask) > 1000
        
        return {
            "signature_detected": signature_detected,
            "stamp_detected": stamp_detected,
            "image_dimensions": image.size
        }
    
    async def _process_with_layoutlm(self, image: Image.Image, text: str) -> Dict[str, Any]:
        """Process with LayoutLMv3 model, handling long texts by chunking to 512 tokens."""
        try:
            max_length = 512
            # Tokenize the text to count tokens
            words = text.split()
            chunks = [" ".join(words[i:i+max_length]) for i in range(0, len(words), max_length)]
            all_confidences = []
            all_token_counts = 0
            for chunk in chunks:
                encoding = self.processor(image, chunk, return_tensors="pt")
                encoding = {k: v.to(self.device) for k, v in encoding.items()}
                with torch.no_grad():
                    outputs = self.model(**encoding)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                all_confidences.append(predictions.mean().item())
                all_token_counts += predictions.shape[1]
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            return {
                "confidence_scores": avg_confidence,
                "token_predictions": all_token_counts,
                "chunks_processed": len(chunks)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_document_fields(self, text: str, document_type: str) -> Dict[str, Any]:
        """Extract specific fields based on document type"""
        fields = {}
        
        if document_type == "Rent Agreement":
            fields = self._extract_rent_agreement_fields(text)
        elif document_type == "Title Deed":
            fields = self._extract_title_deed_fields(text)
        elif document_type == "NOC":
            fields = self._extract_noc_fields(text)
        
        return fields
    
    def _extract_rent_agreement_fields(self, text: str) -> Dict[str, Any]:
        """Extract rent agreement specific fields"""
        fields = {}

        # Landlord and Tenant
        match = re.search(
            r"""between\s+([A-Za-z\s,]+),\s+herein called\s+[“"'`]?Landlord[”"'`]?,?.*?and\s+([A-Za-z\s,]+),\s+herein called\s+[“"'`]?Tenant[”"'`]?""",
            text,
            re.IGNORECASE | re.DOTALL
        )
        if match:
            fields['landlord'] = match.group(1).strip()
            fields['tenant'] = match.group(2).strip()

        # Property Address
        match = re.search(r'located at ([0-9A-Za-z\s,]+) under the following', text, re.IGNORECASE)
        if match:
            fields['property_address'] = match.group(1).strip()

        # Term (duration)
        match = re.search(r'fixed term of ([a-zA-Z0-9\s]+),', text, re.IGNORECASE)
        if match:
            fields['term'] = match.group(1).strip()

        # Rent Amount
        match = re.search(r'sum of \$([0-9,]+) per month', text, re.IGNORECASE)
        if match:
            fields['rent_amount'] = f"${match.group(1).strip()}"

        # Security Deposit
        match = re.search(r'security deposit of \$([0-9,]+)', text, re.IGNORECASE)
        if match:
            fields['security_deposit'] = f"${match.group(1).strip()}"

        # Rent Due Date
        match = re.search(r'payable monthly in advance on the ([0-9A-Za-z]+ day) of each month', text, re.IGNORECASE)
        if match:
            fields['rent_due_date'] = match.group(1).strip()

        return fields
    
    def _extract_title_deed_fields(self, text: str) -> Dict[str, Any]:
        """Extract title deed specific fields"""
        fields = {}
        
        # Extract owner name
        owner_pattern = r"(?:owner|proprietor)[:\s]+([A-Za-z\s]+)"
        owner_match = re.search(owner_pattern, text, re.IGNORECASE)
        if owner_match:
            fields['owner'] = owner_match.group(1).strip()
        
        # Extract property details
        property_pattern = r"(?:property|plot)[:\s]+([A-Za-z0-9\s,.-]+)"
        property_match = re.search(property_pattern, text, re.IGNORECASE)
        if property_match:
            fields['property_details'] = property_match.group(1).strip()
        
        return fields
    
    def _extract_noc_fields(self, text: str) -> Dict[str, Any]:
        """Extract NOC specific fields"""
        fields = {}
        
        # Extract applicant name
        applicant_pattern = r"(?:applicant|name)[:\s]+([A-Za-z\s]+)"
        applicant_match = re.search(applicant_pattern, text, re.IGNORECASE)
        if applicant_match:
            fields['applicant'] = applicant_match.group(1).strip()
        
        # Extract purpose
        purpose_pattern = r"(?:purpose|reason)[:\s]+([A-Za-z\s]+)"
        purpose_match = re.search(purpose_pattern, text, re.IGNORECASE)
        if purpose_match:
            fields['purpose'] = purpose_match.group(1).strip()
        
        return fields
