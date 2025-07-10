import asyncio
import json
from typing import Dict, List, Any
import requests
import re

class LLMReasoner:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "llama3.2:3b"
        self.ready = False
    
    async def initialize(self):
        """Initialize connection to Ollama"""
        try:
            # Test connection
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                self.ready = True
                print("LLM Reasoner initialized successfully")
            else:
                print("Ollama service not available")
                self.ready = False
        except Exception as e:
            print(f"Error initializing LLM: {e}")
            self.ready = False
    
    def is_ready(self) -> bool:
        return self.ready
    
    async def analyze_document(self, extracted_data: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Analyze document and return structured assessment"""
        try:
            # Create analysis prompt
            prompt = self._create_analysis_prompt(extracted_data, document_type)
            
            # Get LLM response
            llm_response = await self._query_ollama(prompt)
            
            # Parse and structure response
            analysis = self._parse_llm_response(llm_response, document_type, extracted_data)
            
            return analysis
            
        except Exception as e:
            raise Exception(f"LLM analysis error: {str(e)}")
    
    def _create_analysis_prompt(self, extracted_data: Dict[str, Any], document_type: str) -> str:
        """Create analysis prompt for LLM"""
        base_prompt = f"""
        Analyze the following {document_type} document and provide a detailed assessment.
        
        Document Text: {extracted_data.get('raw_text', '')}
        
        Extracted Fields: {json.dumps(extracted_data.get('extracted_fields', {}), indent=2)}
        
        Layout Analysis: {json.dumps(extracted_data.get('layout_data', {}), indent=2)}
        
        Please provide analysis in the following format:
        """
        
        if document_type == "Rent Agreement":
            prompt = base_prompt + """
            BENEFITS: List all positive aspects and legally compliant elements
            RISKS: List all missing clauses, legal risks, or concerns
            COMPLETENESS: Rate completeness as a percentage
            SUMMARY: Provide key details in structured format
            
            Focus on:
            - 11-month lease clause compliance
            - Stamp duty presence
            - Signature verification
            - Essential clauses (rent, deposit, maintenance)
            - Legal compliance
            """
        elif document_type == "Title Deed":
            prompt = base_prompt + """
            BENEFITS: List all positive aspects and legally compliant elements
            RISKS: List all missing clauses, legal risks, or concerns
            COMPLETENESS: Rate completeness as a percentage
            SUMMARY: Provide key details in structured format
            
            Focus on:
            - Clear title verification
            - Boundary details
            - Registration compliance
            - Encumbrance status
            - Legal documentation
            """
        elif document_type == "NOC":
            prompt = base_prompt + """
            BENEFITS: List all positive aspects and legally compliant elements
            RISKS: List all missing clauses, legal risks, or concerns
            COMPLETENESS: Rate completeness as a percentage
            SUMMARY: Provide key details in structured format
            
            Focus on:
            - Authority signature verification
            - Purpose clarity
            - Validity period
            - Conditions and restrictions
            - Legal authorization
            """
        
        return prompt
    
    async def _query_ollama(self, prompt: str) -> str:
        """Query Ollama API"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(self.ollama_url, json=payload)
            response.raise_for_status()
            
            return response.json()["response"]
            
        except Exception as e:
            raise Exception(f"Ollama query error: {str(e)}")
    
    def _parse_llm_response(self, response: str, document_type: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        try:
            # Extract sections from response
            benefits = self._extract_section(response, "BENEFITS")
            risks = self._extract_section(response, "RISKS")
            completeness = self._extract_completeness(response)
            
            # Create summary based on extracted fields
            summary = self._create_summary(extracted_data, document_type)
            
            return {
                "summary": summary,
                "benefits": benefits,
                "risks": risks,
                "completeness_score": completeness,
                "confidence_score": min(0.95, max(0.60, completeness / 100))
            }
            
        except Exception as e:
            # Fallback response
            return self._create_fallback_response(extracted_data, document_type)
    
    def _extract_section(self, response: str, section_name: str) -> List[str]:
        """Extract specific section from LLM response"""
        pattern = f"{section_name}:(.+?)(?=RISKS:|COMPLETENESS:|SUMMARY:|$)"
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        
        if match:
            content = match.group(1).strip()
            # Split by lines and clean up
            items = [item.strip("- ").strip() for item in content.split('\n') if item.strip()]
            return [item for item in items if len(item) > 10]  # Filter out short items
        
        return []
    
    def _extract_completeness(self, response: str) -> float:
        """Extract completeness percentage from response"""
        pattern = r"(\d+)%"
        matches = re.findall(pattern, response)
        
        if matches:
            return float(matches[0])
        
        return 75.0  # Default value
    
    def _create_summary(self, extracted_data: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Create summary based on extracted fields"""
        fields = extracted_data.get('extracted_fields', {})
        layout = extracted_data.get('layout_data', {})
        
        summary = {
            "signaturePresent": layout.get('signature_detected', False),
            "stampDutyDetected": layout.get('stamp_detected', False),
            "documentType": document_type
        }
        
        if document_type == "Rent Agreement":
            summary.update({
                "landlord": fields.get('landlord', 'Not detected'),
                "tenant": fields.get('tenant', 'Not detected'),
                "propertyAddress": fields.get('property_address', 'Not detected'),
                "term": fields.get('term', 'Not detected'),
                "rentAmount": fields.get('rent_amount', 'Not detected')
            })
        elif document_type == "Title Deed":
            summary.update({
                "owner": fields.get('owner', 'Not detected'),
                "propertyDetails": fields.get('property_details', 'Not detected')
            })
        elif document_type == "NOC":
            summary.update({
                "applicant": fields.get('applicant', 'Not detected'),
                "purpose": fields.get('purpose', 'Not detected')
            })
        
        return summary
    
    def _create_fallback_response(self, extracted_data: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Create fallback response when LLM parsing fails"""
        summary = self._create_summary(extracted_data, document_type)
        
        return {
            "summary": summary,
            "benefits": ["Document uploaded successfully", "Basic information extracted"],
            "risks": ["Unable to perform detailed analysis", "Manual review recommended"],
            "completeness_score": 60.0,
            "confidence_score": 0.60
        }
