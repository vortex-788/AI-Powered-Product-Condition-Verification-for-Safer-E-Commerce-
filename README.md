# VeriShield 🛡️

**AI-Powered Product Condition Verification for Safer E-Commerce**

> Detect damage, prevent return fraud, and build trust between buyers and sellers using advanced computer vision AI.

## Features

- 🔍 **AI Damage Detection** — Scratches, cracks, dents, wear scoring (0–100)
- 🎥 **Video Verification** — Frame-by-frame analysis of product condition
- 🛂 **Digital Product Passport** — Unique ID + full verification history
- 🚨 **Return Fraud Detection** — SSIM + ORB + histogram comparison to catch swaps
- 📊 **Verification Dashboard** — Real-time monitoring of all products

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + TailwindCSS |
| Backend | Node.js + Express + Mongoose |
| AI Service | Python + FastAPI + OpenCV + TensorFlow |
| Database | MongoDB |

## Quick Start

```bash
# 1. Backend
cd backend && npm install && npm run dev

# 2. AI Service
cd ai-service && pip install -r requirements.txt && python main.py

# 3. Frontend
cd frontend && npm install && npm run dev
```

Open http://localhost:3000 in your browser.

## Project Structure

```
├── backend/          # Express API (port 5000)
├── ai-service/       # FastAPI AI engine (port 8000)
├── frontend/         # React SPA (port 3000)
└── docs/             # Documentation
```

## Documentation

- [Deployment Guide](docs/deployment.md)
- [Business Model & Pitch](docs/business-model.md)

## License

MIT
