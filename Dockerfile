# Use official Python image
FROM python:3.10-slim

# Set working directory
# CACHEBUST=v20.105-FINAL-AUDIT
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Copy requirements from the subfolder
COPY voter_api/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code from subfolder to /app
COPY voter_api/ .
RUN mkdir -p static

# Run the application using uvicorn directly for better Cloud Run compatibility
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
