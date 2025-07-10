from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime

class DocumentAnalysis(BaseModel):
    documentType: str
    filename: str
    uploadTime: datetime
    analysis: Dict[str, Any]
    status: str

class RentAgreementSummary(BaseModel):
    landlord: str
    tenant: str
    propertyAddress: str
    term: str
    rentAmount: str
    signaturePresent: bool
    stampDutyDetected: bool
    confidenceScore: float

class TitleDeedSummary(BaseModel):
    owner: str
    propertyDetails: str
    signaturePresent: bool
    stampDutyDetected: bool
    confidenceScore: float

class NOCSummary(BaseModel):
    applicant: str
    purpose: str
    signaturePresent: bool
    stampDutyDetected: bool
    confidenceScore: float

class AnalysisResult(BaseModel):
    summary: Dict[str, Any]
    benefits: List[str]
    risks: List[str]
    completeness_score: float
    confidence_score: float
