FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable live logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Install required system libraries for OpenCV, PaddlePaddle and ReportLab
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependencies first for faster Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Ensure empty runtime folders exist
RUN mkdir -p uploads reports

EXPOSE 8000

# Run Uvicorn using the PORT environment variable passed by Render / Railway
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
