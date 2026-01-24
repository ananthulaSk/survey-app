# Use official Python image
FROM python:3.10-slim

# Set working directory
# CACHEBUST=v19.29-SAFETY
WORKDIR /app

# Copy requirements from the subfolder
COPY voter_api/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code (including static/flutter_app) from subfolder to /app
COPY voter_api/ .

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
