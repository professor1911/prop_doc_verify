import streamlit as st
import requests
import json
import pandas as pd
from typing import Dict, Any
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page config
st.set_page_config(
    page_title="Property Document Verifier",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .benefit-card {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .risk-card {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .summary-card {
        background-color: #e2e3e5;
        border: 1px solid #d6d8db;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None

# Backend URL
BACKEND_URL = "http://localhost:8080"

def main():
    st.markdown('<h1 class="main-header">🏠 Property Document Verifier</h1>', unsafe_allow_html=True)
    
    # Sidebar - Left Pane
    with st.sidebar:
        st.header("📄 Document Upload")
        
        # Document type selection
        document_type = st.selectbox(
            "Select Document Type",
            ["Rent Agreement", "Title Deed", "NOC"],
            index=0
        )
        
        # Dynamic file upload based on document type
        file_formats = get_allowed_formats(document_type)
        st.info(f"Supported formats: {', '.join(file_formats)}")
        
        uploaded_file = st.file_uploader(
            f"Upload {document_type}",
            type=file_formats,
            key="document_upload"
        )
        
        # Process button
        if st.button("🔍 Analyze Document", type="primary"):
            if uploaded_file:
                with st.spinner("Processing document..."):
                    result = process_document(uploaded_file, document_type)
                    if result:
                        st.session_state.analysis_result = result
                        st.session_state.uploaded_file = uploaded_file
                        st.success("Document processed successfully!")
                    else:
                        st.error("Failed to process document")
            else:
                st.warning("Please upload a document first")
    
    # Main Panel - Right Pane
    if st.session_state.analysis_result:
        display_analysis_results(st.session_state.analysis_result)
    else:
        display_welcome_message()

def get_allowed_formats(document_type: str) -> list:
    """Get allowed file formats for document type"""
    formats_map = {
        "Rent Agreement": ["pdf", "jpg", "png"],
        "Title Deed": ["pdf", "jpg", "png"],
        "NOC": ["pdf", "jpg", "png"]
    }
    return formats_map.get(document_type, ["pdf"])

def process_document(uploaded_file, document_type: str) -> Dict[str, Any]:
    """Process document via backend API"""
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        data = {"document_type": document_type}
        
        response = requests.post(
            f"{BACKEND_URL}/upload-document",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
            
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

def display_analysis_results(result: Dict[str, Any]):
    """Display analysis results in structured format"""
    analysis = result.get('analysis', {})
    summary = analysis.get('summary', {})
    benefits = analysis.get('benefits', [])
    risks = analysis.get('risks', [])
    
    # Top Section - Document Summary
    st.header("📋 Document Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔍 Key Details")
        display_document_summary(summary, result['documentType'])
    
    with col2:
        st.subheader("📊 Analysis Scores")
        display_confidence_scores(analysis)
    
    # Bottom Section - Benefits and Risks
    st.header("⚖️ Legal Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ Benefits & Compliance")
        display_benefits(benefits)
    
    with col2:
        st.subheader("❌ Risks & Concerns")
        display_risks(risks)
    
    # JSON Export
    st.header("🔧 Technical Details")
    with st.expander("View Raw JSON"):
        st.json(result)

def display_document_summary(summary: Dict[str, Any], document_type: str):
    """Display document summary based on type"""
    if document_type == "Rent Agreement":
        display_rent_agreement_summary(summary)
    elif document_type == "Title Deed":
        display_title_deed_summary(summary)
    elif document_type == "NOC":
        display_noc_summary(summary)

def display_rent_agreement_summary(summary: Dict[str, Any]):
    """Display rent agreement specific summary"""
    data = {
        "Field": ["Landlord", "Tenant", "Property Address", "Term", "Rent Amount", "Signature", "Stamp Duty"],
        "Value": [
            summary.get('landlord', 'N/A'),
            summary.get('tenant', 'N/A'),
            summary.get('propertyAddress', 'N/A'),
            summary.get('term', 'N/A'),
            summary.get('rentAmount', 'N/A'),
            "✅ Present" if summary.get('signaturePresent') else "❌ Missing",
            "✅ Present" if summary.get('stampDutyDetected') else "❌ Missing"
        ]
    }
    
    df = pd.DataFrame(data)
    st.table(df)

def display_title_deed_summary(summary: Dict[str, Any]):
    """Display title deed specific summary"""
    data = {
        "Field": ["Owner", "Property Details", "Signature", "Stamp Duty"],
        "Value": [
            summary.get('owner', 'N/A'),
            summary.get('propertyDetails', 'N/A'),
            "✅ Present" if summary.get('signaturePresent') else "❌ Missing",
            "✅ Present" if summary.get('stampDutyDetected') else "❌ Missing"
        ]
    }
    
    df = pd.DataFrame(data)
    st.table(df)

def display_noc_summary(summary: Dict[str, Any]):
    """Display NOC specific summary"""
    data = {
        "Field": ["Applicant", "Purpose", "Signature", "Stamp Duty"],
        "Value": [
            summary.get('applicant', 'N/A'),
            summary.get('purpose', 'N/A'),
            "✅ Present" if summary.get('signaturePresent') else "❌ Missing",
            "✅ Present" if summary.get('stampDutyDetected') else "❌ Missing"
        ]
    }
    
    df = pd.DataFrame(data)
    st.table(df)

def display_confidence_scores(analysis: Dict[str, Any]):
    """Display confidence scores with visual indicators"""
    confidence = analysis.get('confidence_score', 0.0)
    completeness = analysis.get('completeness_score', 0.0)
    
    # Confidence Score
    st.metric("Confidence Score", f"{confidence:.2%}")
    st.progress(confidence)
    
    # Completeness Score
    st.metric("Completeness", f"{completeness:.1f}%")
    st.progress(completeness / 100)

def display_benefits(benefits: list):
    """Display benefits in green cards"""
    if benefits:
        for benefit in benefits:
            st.markdown(f"""
            <div class="benefit-card">
                <strong>✅ {benefit}</strong>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No specific benefits identified")

def display_risks(risks: list):
    """Display risks in red cards"""
    if risks:
        for risk in risks:
            st.markdown(f"""
            <div class="risk-card">
                <strong>❌ {risk}</strong>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No significant risks identified")

def display_welcome_message():
    """Display welcome message when no document is uploaded"""
    st.markdown("""
    ## Welcome to Property Document Verifier! 🏠
    
    This AI-powered tool helps you verify and analyze property documents including:
    
    - **Rent Agreements**: Check for legal compliance, terms, and completeness
    - **Title Deeds**: Verify ownership and property details
    - **NOC (No Objection Certificate)**: Validate authorization and conditions
    
    ### How it works:
    1. Select your document type from the sidebar
    2. Upload your document (PDF, JPG, or PNG)
    3. Click "Analyze Document" to process
    4. Review the detailed analysis with benefits and risks
    
    ### Features:
    - **VLM Processing**: Advanced document understanding using LayoutLMv3
    - **LLM Analysis**: Legal reasoning with Ollama 3.2 3B model
    - **Risk Assessment**: Identify missing clauses and legal concerns
    - **Confidence Scoring**: Get reliability metrics for the analysis
    
    **Get started by uploading a document! 👆**
    """)

if __name__ == "__main__":
    main()
