FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY frontend/ ./frontend/
COPY tests/ ./tests/

# Create uploads directory
RUN mkdir -p uploads

# Expose ports
EXPOSE 8000 8501

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting Property Document Verifier..."\n\
\n\
# Start FastAPI backend in background\n\
echo "Starting FastAPI backend on port 8000..."\n\
cd /app && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &\n\
\n\
# Wait for backend to start\n\
sleep 5\n\
\n\
# Start Streamlit frontend\n\
echo "Starting Streamlit frontend on port 8501..."\n\
cd /app && streamlit run frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0\n\
' > /app/start.sh && chmod +x /app/start.sh

# Set the startup command
CMD ["/app/start.sh"]
