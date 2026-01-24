# Technical Stack Documentation

## Overview
The application is a modern web-based survey platform built with a high-performance FastAPI backend and a responsive Flutter Web frontend. It is containerized using Docker and deployed on Google Cloud Run with a fully automated CI/CD pipeline.

## 1. Backend Layer
- **Framework:** FastAPI (Python 3.10) - chosen for async support and auto swagger docs.
- **Server:** Uvicorn (ASGI Server).
- **Database ORM:** SQLAlchemy (Async sessions).
- **Data Validation:** Pydantic.
- **Key Libraries:** `requests` (API calls), `python-multipart` (Form/File handling).

## 2. Frontend Layer (Web & Mobile)
- **Framework:** Flutter (SDK ^3.10.4) compiled to Web (HTML/CSS/Wasm/JS).
- **Language:** Dart.
- **Key Packages:**
  - `http` (^1.1.0): Backend communication.
  - `fl_chart` (^0.70.2): Visualization and analytics charts.
  - `shared_preferences` (^2.5.4): Local session storage.
  - `cupertino_icons` & `flutter_lints`: UI assets and code quality.

## 3. Infrastructure & DevOps
- **Containerization:** Docker (Base: `python:3.10-slim`). Multi-stage build.
- **Cloud Platform:** Google Cloud Run (Serverless, Auto-scaling).
- **CI/CD:** Google Cloud Build (`cloudbuild.yaml`).
- **Region:** asia-south1 (Mumbai).
