import pytest
import asyncio
import os
import sys
from pathlib import Path

# Add app directory to path
sys.path.append(str(Path(__file__).parent.parent / "app"))

from vlm_processor import VLMProcessor
from llm_reasoner import LLMReasoner

class TestPropertyDocumentVerifier:
    
    @pytest.fixture
    async def vlm_processor(self):
        processor = VLMProcessor()
        await processor.initialize()
        return processor
    
    @pytest.fixture
    async def llm_reasoner(self):
        reasoner = LLMReasoner()
        await reasoner.initialize()
        return reasoner
    
    @pytest.mark.asyncio
    async def test_rent_agreement_processing(self, vlm_processor, llm_reasoner):
        """Test complete rent agreement processing"""
        # Mock extracted data for complete rent agreement
        mock_data = {
            "raw_text": """
            RENT AGREEMENT
            
            This agreement is made between Mr. Ramesh Sharma (Landlord) and 
            Mr. Vaibhav Kulkarni (Tenant) for the property located at 
            Flat 4B, Krishna Tower, Andheri East, Mumbai.
            
            Term: 11 months
            Rent Amount: Rs. 22,000 per month
            Security Deposit: Rs. 44,000
            
            Signatures:
            Landlord: [Signed]
            Tenant: [Signed]
            """,
            "layout_data": {
                "signature_detected": True,
                "stamp_detected": True,
                "image_dimensions": (800, 1200)
            },
            "extracted_fields": {
                "landlord": "Ramesh Sharma",
                "tenant": "Vaibhav Kulkarni",
                "property_address": "Flat 4B, Krishna Tower, Andheri East, Mumbai",
                "term": "11 months",
                "rent_amount": "₹22,000"
            }
        }
        
        # Test LLM analysis
        result = await llm_reasoner.analyze_document(mock_data, "Rent Agreement")
        
        assert result is not None
        assert "summary" in result
        assert "benefits" in result
        assert "risks" in result
        assert result["summary"]["landlord"] == "Ramesh Sharma"
        assert result["summary"]["tenant"] == "Vaibhav Kulkarni"
        assert result["summary"]["signaturePresent"] == True
        assert result["summary"]["stampDutyDetected"] == True
    
    @pytest.mark.asyncio
    async def test_title_deed_incomplete(self, llm_reasoner):
        """Test title deed with missing information"""
        mock_data = {
            "raw_text": """
            TITLE DEED
            
            Owner: John Smith
            Property: House No. 123, ABC Street
            
            [Missing boundary details]
            [Missing registration details]
            """,
            "layout_data": {
                "signature_detected": False,
                "stamp_detected": False,
                "image_dimensions": (800, 1200)
            },
            "extracted_fields": {
                "owner": "John Smith",
                "property_details": "House No. 123, ABC Street"
            }
        }
        
        result = await llm_reasoner.analyze_document(mock_data, "Title Deed")
        
        assert result is not None
        assert result["summary"]["signaturePresent"] == False
        assert result["summary"]["stampDutyDetected"] == False
        assert len(result["risks"]) > 0  # Should have identified missing elements
    
    @pytest.mark.asyncio
    async def test_noc_signature_issues(self, llm_reasoner):
        """Test NOC with signature issues"""
        mock_data = {
            "raw_text": """
            NO OBJECTION CERTIFICATE
            
            Applicant: Sarah Johnson
            Purpose: Construction of additional floor
            
            Authority: Municipal Corporation
            
            [Signature area appears blank]
            """,
            "layout_data": {
                "signature_detected": False,
                "stamp_detected": True,
                "image_dimensions": (800, 1200)
            },
            "extracted_fields": {
                "applicant": "Sarah Johnson",
                "purpose": "Construction of additional floor"
            }
        }
        
        result = await llm_reasoner.analyze_document(mock_data, "NOC")
        
        assert result is not None
        assert result["summary"]["signaturePresent"] == False
        assert result["summary"]["stampDutyDetected"] == True
        assert any("signature" in risk.lower() for risk in result["risks"])

# Mock test data generator
def create_mock_test_files():
    """Create mock test files for testing"""
    test_documents = {
        "rent_agreement_complete.json": {
            "documentType": "Rent Agreement",
            "summary": {
                "landlord": "Ramesh Sharma",
                "tenant": "Vaibhav Kulkarni",
                "propertyAddress": "Flat 4B, Krishna Tower, Andheri East, Mumbai",
                "term": "11 months",
                "rentAmount": "₹22,000",
                "signaturePresent": True,
                "stampDutyDetected": True,
                "confidenceScore": 0.91
            },
            "benefits": [
                "Legally binding 11-month term clause",
                "Valid stamp duty present",
                "Signatures present from both parties",
                "Clear rent amount specified",
                "Property address clearly mentioned"
            ],
            "risks": [
                "No early termination clause specified",
                "Missing witness signatures"
            ]
        },
        "title_deed_incomplete.json": {
            "documentType": "Title Deed",
            "summary": {
                "owner": "John Smith",
                "propertyDetails": "House No. 123, ABC Street",
                "signaturePresent": False,
                "stampDutyDetected": False,
                "confidenceScore": 0.65
            },
            "benefits": [
                "Owner name clearly specified",
                "Property address mentioned"
            ],
            "risks": [
                "Missing boundary details",
                "No registration number present",
                "Signatures not detected",
                "Stamp duty not present",
                "Missing encumbrance certificate details"
            ]
        },
        "noc_signature_issues.json": {
            "documentType": "NOC",
            "summary": {
                "applicant": "Sarah Johnson",
                "purpose": "Construction of additional floor",
                "signaturePresent": False,
                "stampDutyDetected": True,
                "confidenceScore": 0.70
            },
            "benefits": [
                "Purpose clearly stated",
                "Applicant name present",
                "Stamp duty detected"
            ],
            "risks": [
                "Authority signature missing",
                "No validity period mentioned",
                "Missing conditions and restrictions",
                "Authorization unclear"
            ]
        }
    }
    
    return test_documents

if __name__ == "__main__":
    # Create mock test files
    test_data = create_mock_test_files()
    
    # Save test files
    test_dir = Path("tests/test_documents")
    test_dir.mkdir(exist_ok=True)
    
    for filename, data in test_data.items():
        with open(test_dir / filename, 'w') as f:
            import json
            json.dump(data, f, indent=2)
    
    print("Mock test files created successfully!")
