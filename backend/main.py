import asyncio
import json
import time
import math
import threading
import numpy as np
from collections import deque
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import paho.mqtt.client as mqtt
from fastapi.responses import FileResponse

# --- Background Task Setup ---
optimization_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global optimization_task
    # Startup: Initialize MQTT Client
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    mqtt_client.on_message = on_message
    
    try:
        mqtt_client.connect("localhost", 1883, 60)
        mqtt_client.subscribe("mine/telemetry")
        mqtt_client.loop_start()
        print("MQTT Client connected and loop started.")
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")
        
    # Start the background physics-informed ML loop
    optimization_task = asyncio.create_task(optimization_loop())
    
    yield
    
    # Teardown: Graceful shutdown
    if optimization_task:
        optimization_task.cancel()
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    print("MQTT Client disconnected and ML loop stopped.")

app = FastAPI(title="Mine Subsidence Prediction Brain", lifespan=lifespan)

# --- Configuration & State ---
class ConfigModel(BaseModel):
    H: float = 0.004
    E_max: float = 0.04
    extraction_rate: float = 0.2
    distance_x: float = 0.20
    flex_baseline: float = 10000.0
    flex_multiplier: float = 0.002

app_config = {
    "H": 0.004,
    "E_max": 0.00059,
    "extraction_rate": 0.2,
    "distance_x": 0.20,
    "flex_baseline": 113000.0,
    "flex_multiplier": 0.000002
}

BUFFER_SIZE = 400
sensor_buffer = deque(maxlen=BUFFER_SIZE)
buffer_lock = threading.Lock()

current_sensor_state = {
    1: {"total_tilt": 0.0, "flex_resistance": 0.0, "last_time": 0.0},
    2: {"total_tilt": 0.0, "flex_resistance": 0.0, "last_time": 0.0}
}

# --- WebSocket Managers ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d)

frontend_manager = ConnectionManager()

# --- MQTT Setup ---
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        node_id = payload.get("node_id")
        
        if node_id in current_sensor_state:
            pitch = float(payload.get("pitch_angle", 0.0))
            roll = float(payload.get("roll_angle", 0.0))
            flex_resistance = float(payload.get("flex_resistance", 0.0))
            
            total_tilt = math.sqrt(pitch**2 + roll**2)
            
            current_sensor_state[node_id]["total_tilt"] = total_tilt
            current_sensor_state[node_id]["flex_resistance"] = flex_resistance
            current_sensor_state[node_id]["last_time"] = time.time()
            
            # Use data from either node 1 or 2 for flex resistance (fallback to the other if one is 0)
            n1_tilt = current_sensor_state[1]["total_tilt"]
            n1_flex = current_sensor_state[1]["flex_resistance"]
            n2_tilt = current_sensor_state[2]["total_tilt"]
            n2_flex = current_sensor_state[2]["flex_resistance"]
            
            merged_snapshot = {
                "timestamp": time.time(),
                "node1_tilt": n1_tilt if n1_tilt > 0 else n2_tilt,
                "node1_flex_resistance": n1_flex if n1_flex > 0 else n2_flex,
                "node2_tilt": n2_tilt if n2_tilt > 0 else n1_tilt,
                "node2_flex_resistance": n2_flex if n2_flex > 0 else n1_flex
            }
            with buffer_lock:
                sensor_buffer.append(merged_snapshot)
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        pass

# --- AI Optimization Loop ---
async def optimization_loop():
    # Absolute anchor to ensure the exponent baseline never shifts
    global_min_strain = None
    
    while True:
        await asyncio.sleep(1.0)
        
        with buffer_lock:
            if len(sensor_buffer) < 15:
                continue
            raw_data = list(sensor_buffer)
        
        data = []
        last_ts = 0.0
        for d in raw_data:
            if d["timestamp"] - last_ts > 1e-3:
                data.append(d)
                last_ts = d["timestamp"]
                
        if len(data) < 15:
            continue
        
        timestamps = np.array([d["timestamp"] for d in data])
        tilt1_array = np.array([d["node1_tilt"] for d in data])
        tilt2_array = np.array([d["node2_tilt"] for d in data])
        flex1_res_array = np.array([d["node1_flex_resistance"] for d in data])
        flex2_res_array = np.array([d["node2_flex_resistance"] for d in data])

        # Normalize flex sensors to the same baseline (Node A: 113k, Node B: 700k)
        kflex_a = 1.0
        kflex_b = 113000.0 / 700000.0
        
        flex1_res_array = flex1_res_array * kflex_a
        flex2_res_array = flex2_res_array * kflex_b
        
        H = app_config["H"]
        E_max = app_config["E_max"]
        distance_x = app_config["distance_x"]
        
        dist_x_safe = distance_x if distance_x > 0 else 1.0 
        tilt_diff_rad = np.abs(tilt1_array - tilt2_array) * (np.pi / 180.0)
        macro_strain_array = (H / 2.0) * (tilt_diff_rad / dist_x_safe)
        
        # Calculate macro acceleration purely for the UI dashboard (not for AI triggers)
        macro_velocity = np.gradient(macro_strain_array, timestamps)
        macro_acceleration = np.gradient(macro_velocity, timestamps)
        
        micro_strain_array = H * app_config["flex_multiplier"] * (flex1_res_array - app_config["flex_baseline"])
        current_micro_strain = micro_strain_array[-1]
        
        micro_strain_array_n2 = H * app_config["flex_multiplier"] * (flex2_res_array - app_config["flex_baseline"])
        current_micro_strain_n2 = micro_strain_array_n2[-1]
        
        # Lock in the global minimum strain reference forever
        if global_min_strain is None:
            global_min_strain = np.min(micro_strain_array)
        else:
            global_min_strain = min(global_min_strain, np.min(micro_strain_array))

        danger_level = 0.0
        time_to_failure = None
        
        # -------------------------------------------------------------
        # EXACT ANALYTICAL SOLVING (Optimized for Pure Exponential Curves)
        # -------------------------------------------------------------
        
        # Slice only the most recent 10 seconds (100 frames at 10Hz) for math fit
        # This prevents flat "secondary creep" data from skewing the active curve
        FIT_LENGTH = min(100, len(timestamps))
        time_slice = timestamps[-FIT_LENGTH:]
        strain_slice = micro_strain_array[-FIT_LENGTH:]
        
        # Reset relative time to the exact start of this 10-second window
        t_data = time_slice - time_slice[0]
        strain_0 = global_min_strain - 1e-6 
        
        y_lin = np.log(np.maximum(strain_slice - strain_0, 1e-12))
        
        # np.polyfit solves exactly without iterative guessing
        coeffs = np.polyfit(t_data, y_lin, 1)
        k_opt = coeffs[0]
        B_opt = np.exp(coeffs[1])
        
        if current_micro_strain >= E_max or strain_0 >= E_max:
            danger_level = 100.0
            time_to_failure = 0.0
            
        # Only start the UI timer if k > 0.005 (The curve has officially bent upwards into tertiary)
        elif k_opt > 0.005 and B_opt > 1e-9:
            term = (E_max - strain_0) / B_opt
            
            if term > 0:
                t_failure_rel = math.log(term) / k_opt
                # Add the relative time back to the absolute timestamp of the window start
                t_failure_abs = time_slice[0] + t_failure_rel
                
                time_to_failure = t_failure_abs - time.time()
                
                if time_to_failure <= 0:
                    danger_level = 100.0
                    time_to_failure = 0.0
                else:
                    # Linear Danger Mapping anchored to a 60-second action window
                    WARNING_WINDOW = 60.0
                    val = time_to_failure / WARNING_WINDOW
                    danger_level = max(0.0, min(100.0, 100.0 * (1 - val)))
                            
        frontend_payload = {
            "timestamp": time.time(),
            "macro_acceleration": round(macro_acceleration[-1], 6),
            "micro_strain_live": round(current_micro_strain, 6),
            "micro_strain_node1": round(current_micro_strain, 6),
            "micro_strain_node2": round(current_micro_strain_n2, 6),
            "node1_tilt": float(tilt1_array[-1]),
            "node2_tilt": float(tilt2_array[-1]),
            "node1_flex": float(flex1_res_array[-1]),
            "node2_flex": float(flex2_res_array[-1]),
            "danger_level": round(danger_level, 2),
            "time_to_failure_s": round(time_to_failure, 2) if time_to_failure is not None and time_to_failure > 0 else None
        }
        await frontend_manager.broadcast(frontend_payload)

# --- FastAPI Routes ---
@app.post("/config")
async def update_config(config: ConfigModel):
    app_config.update(config.model_dump())
    return {"message": "Configuration updated successfully", "current_config": app_config}

@app.websocket("/ws/frontend")
async def websocket_frontend(websocket: WebSocket):
    await frontend_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        frontend_manager.disconnect(websocket)

@app.get("/")
async def get_dashboard():
    return FileResponse("dashboard.html")

@app.get("/v2")
async def get_dashboard_v2():
    return FileResponse("dashboard2.html")
