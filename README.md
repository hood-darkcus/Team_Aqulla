# 🪨 Mine Subsidence Monitoring & Early Warning System (Backend)

A real-time, physics-informed AI backend designed to monitor structural integrity and predict roof subsidence in coal mines. This system ingests live telemetry from hardware sensor nodes (flex and tilt sensors), processes kinematics to detect tertiary creep, and mathematically calculates the Time-to-Failure (TTF) before a collapse.

## 🚀 Features

* **Real-Time Telemetry Ingestion:** Uses `Paho-MQTT` to instantly ingest pitch, roll, and flex resistance data from distributed ESP32/LoRa sensor nodes.
* **Physics-Informed Prediction:** Using saito teritiary creep graph based regression model to predict time for failure and danger levels
* **Live Dashboard Streaming:** Utilizes a FastAPI and mqtt manager to broadcast parsed kinematics, Danger Level (0-100%), and TTF directly to the frontend.
* **Noise Filtration:** Implements rolling moving averages, 1-second velocity tripwires, and macro-acceleration gates to mathematically eliminate sensor hallucinations during primary and secondary creep phases.

## 🛠️ Tech Stack

* **Framework:** FastAPI (Python)
* **IoT Protocol:** Paho-MQTT
* **Math & AI Engine:** NumPy, SciPy (`curve_fit`, `polyfit`)
* **Concurrency:** Asyncio, Threading (Lock-protected buffers)

## ⚙️ Prerequisites

Before running this backend, ensure you have the following installed on your machine:
* Python 3.9+
* An active MQTT Broker (e.g., Eclipse Mosquitto) running on `localhost:1883`

## 📦 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/mine-subsidence-backend.git](https://github.com/your-username/mine-subsidence-backend.git)
   cd mine-subsidence-backend
