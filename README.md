# GFB-Vision-Eye

**Type**: Industrial Computer Vision Microservice (Edge-ready)
**Part of**: Global FoodTech Bridge Ecosystem

## Overview

This is an autonomous Computer Vision microservice designed for real-time quality control of prepared food packaging on a conveyor belt. It receives images via API or RTSP stream, processes them using a lightweight YOLO model, and returns a verdict on defects.

## Features

- **Real-time Defect Detection**: Detects 'tear', 'label_error', and 'foreign_object'.
- **Edge Optimized**: Runs on lightweight hardware using standard Docker containers.
- **Clean Architecture**: Separation of concerns for easy maintenance and model swappability.
- **REST API**: Asynchronous FastAPI endpoints for integration with the main logistics system.

## Project Structure

```
GFB-Vision-Eye/
├── app/
│   ├── api/            # API Endpoints (Routers)
│   ├── core/           # Configuration, Logging
│   ├── services/       # Business Logic (Model Inference)
│   ├── schemas/        # Pydantic Models (Request/Response)
│   └── utils/          # Image Processing Utilities
├── models/             # YOLO Model Weights (.pt files)
├── Dockerfile          # Container definition
├── main.py             # Application Entrypoint
├── config.py           # Configuration Loader
└── requirements.txt    # Python Dependencies
```

## Setup & Running

### Prerequisites

- Python 3.10+
- Docker (optional, for containerized run)

### Local Development

1. **Clone the repository**
2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment Configuration**:
   Copy `.env.example` to `.env` and adjust settings.
   ```bash
   cp .env.example .env
   ```
5. **Run the server**:
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Deployment

1. **Build the image**:
   ```bash
   docker build -t gfb-vision-eye .
   ```
2. **Run the container**:
   ```bash
   docker run -p 8000:8000 --env-file .env gfb-vision-eye
   ```

## Configuration

Configuration is managed via environment variables (see `.env.example`). Key variables:

- `MODEL_PATH`: Path to the YOLO .pt file (default: `models/yolo11n.pt`).
- `CONFIDENCE_THRESHOLD`: Minimum confidence score for detection (default: `0.5`).
- `API_V1_STR`: API version prefix (default: `/api/v1`).
