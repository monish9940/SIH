FROM python:3.11-slim

# Install system dependencies required for OpenCV and EasyOCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install CPU-only PyTorch to minimize RAM usage on 512MB free tier
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Limit CPU threads to prevent memory allocation spikes
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV OPENBLAS_NUM_THREADS=1
ENV EASYOCR_MODEL_DIR=/app/models/easyocr

# Create application model and upload directories
RUN mkdir -p /app/models/easyocr /app/uploads

# Copy application code
COPY . .

# Expose port 8000
EXPOSE 8000

# Run Uvicorn server dynamically reading PORT from environment
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
