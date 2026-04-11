# 🔧 Predictive Maintenance for Industrial Machines

> **Real-time IoT-driven machine health monitoring with ML-powered failure prediction.**  
> An end-to-end system: ESP32 sensors → MQTT → FastAPI backend → PostgreSQL → React dashboard.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [ML Model](#ml-model)
- [Hardware Setup](#hardware-setup)
- [Testing](#testing)
- [Deployment](#deployment)
- [Team](#team)
- [Roadmap](#roadmap)

---

## Overview

Industrial machines fail unexpectedly — this project predicts *how* and *when* before it happens.

The system collects sensor data (temperature, RPM, torque, tool wear) from an ESP32 microcontroller, streams it through ThingSpeak MQTT, and runs it through a scikit-learn classifier that identifies one of six failure modes in real time. Results are pushed to a React dashboard via Server-Sent Events (SSE) with sub-5-second latency.

**Failure types detected:**
- ✅ No Failure
- 🌡️ Heat Dissipation Failure
- ⚡ Power Failure
- 💪 Overstrain Failure
- 🔩 Tool Wear Failure
- 🎲 Random Failures

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         ESP32 Firmware                           │
│  DHT11 (temp/humidity) + Hall sensor (RPM) + INA219 (current)   │
│                    MQTT → mqtt3.thingspeak.com                   │
└───────────────────────────┬──────────────────────────────────────┘
                            │ MQTT publish (field1–field5)
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                       ThingSpeak Cloud                           │
│              Buffers readings, exposes REST + MQTT               │
└───────────────────────────┬──────────────────────────────────────┘
                            │ REST poll every 15s (APScheduler)
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend  (Python)                      │
│   IoT Poller │ ML Service (inference) │ REST API + SSE           │
│              └──────────────┘                                    │
│         PostgreSQL + TimescaleDB                                 │
│   sensor_readings table  │  predictions table                    │
└───────────────────────────┬──────────────────────────────────────┘
                            │ REST + SSE
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    React Frontend  (Vite + TS)                   │
│      Live Dashboard  │  Historical Charts  │  Manual Predict     │
└──────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Firmware** | ESP32 + Arduino |
| **IoT Broker** | ThingSpeak MQTT |
| **Backend** | FastAPI (Python 3.11), APScheduler |
| **ML Inference** | scikit-learn (Random Forest) |
| **Database** | PostgreSQL + TimescaleDB |
| **Real-time Push** | Server-Sent Events (SSE) |
| **Frontend** | React 18 + Vite + TypeScript |
| **Charts** | Recharts |
| **Styling** | Tailwind CSS |
| **Containerisation** | Docker + docker-compose |
| **CI/CD** | GitHub Actions |

---

## Project Structure

```
machine-predictive-maintenance/
├── backend/
│   ├── main.py                  # FastAPI app factory
│   ├── config.py                # Settings (pydantic-settings)
│   ├── database.py              # SQLAlchemy async engine
│   ├── models/
│   │   ├── sensor_reading.py
│   │   └── prediction.py
│   ├── schemas/
│   │   ├── sensor.py
│   │   └── prediction.py
│   ├── services/
│   │   ├── ml_service.py        # Single source of truth for inference
│   │   ├── thingspeak.py        # ThingSpeak REST client
│   │   └── iot_poller.py        # APScheduler job
│   ├── routers/
│   │   ├── readings.py
│   │   ├── predictions.py
│   │   └── stream.py            # SSE endpoint
│   ├── ml/
│   │   ├── predictive_maintenance.pkl
│   │   └── scaler.pkl
│   ├── tests/
│   │   ├── test_ml_service.py
│   │   ├── test_preprocessing.py
│   │   └── test_api.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx    # Live gauges + latest prediction
│   │   │   ├── History.tsx      # Date-range charts from DB
│   │   │   └── Predict.tsx      # Manual input form
│   │   ├── components/
│   │   │   ├── GaugeCard.tsx
│   │   │   ├── TrendChart.tsx
│   │   │   ├── PredictionBadge.tsx
│   │   │   └── SensorForm.tsx
│   │   ├── hooks/
│   │   │   ├── useSSE.ts
│   │   │   └── useReadings.ts
│   │   └── lib/api.ts
│   ├── vite.config.ts
│   └── package.json
├── firmware/
│   └── esp32_firmware.cpp
├── ml/
│   ├── train.py
│   ├── evaluate.py
│   └── predictive_maintenance.csv
├── docker-compose.yml
├── .env.example
└── .github/workflows/ci.yml
```

---

## Getting Started

### Prerequisites

- Docker & docker-compose
- Node.js 20+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

### Quick Start (Docker)

```bash
# 1. Clone the repo
git clone https://github.com/your-org/machine-predictive-maintenance.git
cd machine-predictive-maintenance

# 2. Copy and fill in environment variables
cp .env.example .env

# 3. Start the full stack
docker compose up --build
```

Services will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Database:**
```bash
# Start only the DB container
docker compose up db -d
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```env
# Backend
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/maintenance
THINGSPEAK_CHANNEL_ID=your_channel_id
THINGSPEAK_READ_API_KEY=your_api_key
POLL_INTERVAL_SECONDS=15
MODEL_PATH=ml/predictive_maintenance.pkl
SCALER_PATH=ml/scaler.pkl
MODEL_VERSION=v1
CORS_ORIGINS=http://localhost:5173

# Frontend
VITE_API_BASE_URL=http://localhost:8000/v1
```

---

## API Reference

Base URL: `/v1`

### Sensor Readings

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/readings` | Paginated readings with `?from`, `?to`, `?limit` |
| `GET` | `/readings/latest` | Most recent sensor reading |
| `POST` | `/readings` | Manually insert a reading |

### Predictions

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/predictions` | Paginated predictions with date filters |
| `GET` | `/predictions/latest` | Most recent prediction |
| `POST` | `/predict` | Run inference on provided sensor values |

### Live Stream

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/stream` | SSE stream of `reading` and `prediction` events |

**SSE event format:**
```
event: reading
data: {"id": 1, "air_temp_k": 302.1, "rpm": 1487, ...}

event: prediction
data: {"failure_type": "No Failure", "confidence": 0.94}
```

Errors follow [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) (`application/problem+json`).

---

## ML Model

The `MLService` class (`backend/services/ml_service.py`) is the **single source of truth** for all inference. No raw pickle loads exist anywhere else in the codebase.

### Input Features

| Feature | Unit | Source |
|---|---|---|
| Machine type | L / M / H | Manual / IoT |
| Air temperature | Kelvin | ✅ DHT11 sensor |
| Process temperature | Kelvin | ⚠️ Defaulted: `air_temp + 10K` |
| Rotational speed | RPM | ⚠️ Fixed default: 1500 |
| Torque | Nm | ⚠️ Fixed default: 40 |
| Tool wear | Minutes | ⚠️ Incremental counter, resets at 250 |

> **⚠️ Assumed features** are flagged in every API response via `assumed_features: [...]` and shown as a warning badge on the frontend dashboard.

### Inference Pipeline

```python
# 1. Encode machine type  →  L:0, M:1, H:2
# 2. StandardScaler on 5 numeric features
# 3. Concatenate type + scaled features → shape (1, 6)
# 4. model.predict()        → failure_type string
# 5. model.predict_proba()  → confidence score (max class prob)
```

### Retraining

```bash
cd ml
python train.py       # trains and saves new .pkl files
python evaluate.py    # prints classification report
```

---

## Hardware Setup

### Wiring (ESP32)

| Sensor | Interface | Pin |
|---|---|---|
| DHT11 (temp/humidity) | Digital | GPIO4 |
| INA219 (voltage/current) | I²C | SDA: GPIO21, SCL: GPIO22 |

### Recommended Additions (v2 hardware)

- **AS5600** hall effect sensor → real RPM
- **INA219** current sensor → torque proxy
- **MAX6675** thermocouple → process temperature

### Flashing the Firmware

```bash
# Using Arduino IDE or PlatformIO
# Open firmware/esp32_firmware.cpp
# Set Wi-Fi credentials and ThingSpeak channel ID
# Flash to ESP32
```

---

## Testing

```bash
cd backend

# Run all tests
pytest

# With coverage
pytest --cov=. --cov-report=term-missing

# Specific test files
pytest tests/test_ml_service.py
pytest tests/test_api.py
```

**Frontend tests:**
```bash
cd frontend
npm run test
```

### Testing Strategy

| Component | Framework | Key Areas |
|---|---|---|
| Backend API | pytest + unittest | Endpoint validation, MQTT handling, DB CRUD |
| ML Model | pytest + scikit-learn | Accuracy, preprocessing pipeline, edge cases |
| Frontend | Jest + React Testing Library | Component rendering, SSE hook, API integration |
| Database | PyMongo / SQLAlchemy mocking | Queries, data integrity, connection handling |
| IoT | MQTT broker logs, multimeter | Sensor accuracy, publish/subscribe, reconnection |

---

## Deployment

### Docker Compose (Production-like)

```bash
docker compose -f docker-compose.yml up -d
```




