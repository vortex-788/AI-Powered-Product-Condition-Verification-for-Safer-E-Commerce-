# VeriShield — Deployment Guide

## Prerequisites
- **Node.js** v18+ and npm
- **Python** 3.9+ and pip
- **MongoDB** (local or Atlas cloud)
- **FFmpeg** (optional, for advanced video processing)

---

## 1. Backend Setup

```bash
cd backend
cp .env.example .env   # Configure MongoDB URI and AI service URL
npm install
npm run dev             # Starts on http://localhost:5000
```

### Environment Variables (`backend/.env`)
| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 5000 | Backend server port |
| `MONGODB_URI` | `mongodb://localhost:27017/verishield` | MongoDB connection string |
| `AI_SERVICE_URL` | `http://localhost:8000` | Python AI service URL |

---

## 2. AI Service Setup

```bash
cd ai-service
pip install -r requirements.txt
python main.py          # Starts on http://localhost:8000
```

> **Note:** TensorFlow is optional. The system falls back to OpenCV-only detection if TF is unavailable.

View API docs at: `http://localhost:8000/docs`

---

## 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev             # Starts on http://localhost:3000
```

API requests are proxied to `localhost:5000` via Vite config.

---

## 4. Production Build

```bash
# Frontend
cd frontend && npm run build    # Output in dist/

# Backend
cd backend && npm start         # Use PM2 for process management

# AI Service
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 5. Docker (Optional)

Each service can be containerized. Example `docker-compose.yml`:

```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:7
    ports: ["27017:27017"]
    volumes: ["mongo_data:/data/db"]

  backend:
    build: ./backend
    ports: ["5000:5000"]
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/verishield
      - AI_SERVICE_URL=http://ai-service:8000
    depends_on: [mongodb]

  ai-service:
    build: ./ai-service
    ports: ["8000:8000"]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]

volumes:
  mongo_data:
```

---

## 6. Cloud Deployment

| Component | Recommended Platform |
|-----------|---------------------|
| Frontend | Vercel, Netlify, or AWS S3 + CloudFront |
| Backend | Railway, Render, or AWS EC2 |
| AI Service | AWS EC2 (GPU), Google Cloud Run, or Railway |
| MongoDB | MongoDB Atlas (free tier available) |
