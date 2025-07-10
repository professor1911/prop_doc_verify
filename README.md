# Property Document Verifier

AI-powered property document verification system using VLM (Visual Language Model) and LLM (Large Language Model) technologies.

## Features

- **Multi-Document Support**: Rent Agreements, Title Deeds, NOC
- **AI-Powered Analysis**: LayoutLMv3 for document understanding + Ollama 3.2 3B for reasoning
- **Risk Assessment**: Identifies missing clauses and legal concerns
- **Interactive UI**: Streamlit-based web interface with color-coded results
- **RESTful API**: FastAPI backend for document processing

## Quick Start

### Prerequisites

- Python 3.10+
- Docker (optional)
- Ollama (for LLM processing)

### Installation

1. **Clone the repository:**
git clone <repository-url>
cd property-doc-verifier

text

2. **Install dependencies:**
pip install -r requirements.txt

text

3. **Install and start Ollama:**
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
ollama pull llama3.2:3b

text

### Running the Application

#### Option 1: Manual Setup

1. **Start the backend:**
cd app
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

text

2. **Start the frontend:**
cd frontend
streamlit run streamlit_app.py --server.port 8501

text

3. **Access the application:**
- Frontend: http://localhost:8501
- API Documentation: http://localhost:8000/docs

#### Option 2: Docker

docker-compose up -d

text

## Usage

1. **Select Document Type**: Choose from Rent Agreement, Title Deed, or NOC
2. **Upload Document**: Support for PDF, JPG, PNG formats
3. **Analyze**: Click "Analyze Document" to process
4. **Review Results**: 
   - Top section shows extracted document details
   - Bottom section shows benefits (green) and risks (red)

## API Endpoints

- `POST /upload-document`: Upload and analyze document
- `GET /document-types`: Get supported document types
- `GET /health`: Health check

## Architecture

┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Streamlit UI │───▶│ FastAPI │───▶│ Ollama LLM │
│ │ │ Backend │ │ (3.2 3B) │
└─────────────────┘ └─────────────────┘ └─────────────────┘
│
▼
┌─────────────────┐
│ LayoutLMv3 │
│ VLM Processor │
└─────────────────┘

text

## Testing

Run the test suite:
cd tests
python -m pytest test_pipeline.py -v

text

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
🚀 Deployment Instructions
Local Development Setup
Install Ollama and pull the model:

bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
ollama pull llama3.2:3b
Start the backend:

bash
cd app
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
Start the frontend:

bash
cd frontend
streamlit run streamlit_app.py --server.port 8501
Access the application:

Frontend: http://localhost:8501

API docs: http://localhost:8000/docs

Production Deployment
Use Docker Compose for production:

bash
docker-compose up -d
This complete system provides:

✅ Full-stack application with FastAPI backend and Streamlit frontend
✅ VLM processing using LayoutLMv3 for document understanding
✅ LLM reasoning with Ollama 3.2 3B for legal analysis
✅ Structured JSON output with benefits and risks
✅ Color-coded UI exactly as specified
✅ Test cases for all three document types
✅ Docker containerization for easy deployment
✅ Modular design for easy model switching

The system is production-ready and includes comprehensive error handling, logging, and documentation.