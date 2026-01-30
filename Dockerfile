# Use official Python image
FROM python:3.10-slim

# Set working directory
# CACHEBUST=v20.15-RESORTED-VOTER-API
ENV PYTHONUNBUFFERED=1
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
# Run the application using the python script to properly handle PORT env var
CMD ["python", "main.py"]
