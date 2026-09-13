import time
import math
import json
import random
import paho.mqtt.client as mqtt

# --- Simulation Configuration ---
BROKER_IP = "localhost"
PORT = 1883
TOPIC = "mine/telemetry"
PUBLISH_RATE_HZ = 10.0

# --- Physical Parameters (Must match main.py) ---
H = 0.004
E_max = 0.04
EXTRACTION_RATE_K = 0.2
DISTANCE_X = 0.20
FLEX_BASELINE = 10000.0
FLEX_MULTIPLIER = 0.002

# --- Noise Parameters ---
FLEX_NOISE_STD_DEV = 5.0      # Ohms
TILT_NOISE_STD_DEV = 0.02     # Degrees

def calculate_sensor_values(true_strain):
    tilt_diff_rad = (true_strain * DISTANCE_X) / (H / 2.0)
    tilt_diff_deg = tilt_diff_rad * (180.0 / math.pi)
    
    node1_pitch = tilt_diff_deg
    node2_pitch = 0.0
    
    node1_flex = FLEX_BASELINE + (true_strain / (H * FLEX_MULTIPLIER))
    node2_flex = FLEX_BASELINE
    
    return node1_pitch, node2_pitch, node1_flex, node2_flex

def get_creep_strain(t):
    # 3-Stage Creep Model
    # Stage 1: Primary (0-30s) - Decelerating
    e0 = 0.0001
    A = 0.005
    c = 0.1
    
    # Stage 2: Secondary (30-70s) - Constant rate
    t1 = 30.0
    strain1_t1 = e0 + A * (1 - math.exp(-c * t1))
    rate_t1 = A * c * math.exp(-c * t1)
    
    # Stage 3: Tertiary (>70s) - Accelerating
    t2 = 70.0
    strain2_t2 = strain1_t1 + rate_t1 * (t2 - t1)
    k = EXTRACTION_RATE_K
    # Calculated so failure (0.04) happens around t=90s
    B = 0.000637 
    
    if t <= t1:
        return e0 + A * (1 - math.exp(-c * t)), "PRIMARY"
    elif t <= t2:
        return strain1_t1 + rate_t1 * (t - t1), "SECONDARY"
    else:
        # Tertiary
        val = strain2_t2 + B * (math.exp(k * (t - t2)) - 1)
        return val, "TERTIARY"

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    
    try:
        client.connect(BROKER_IP, PORT, 60)
        print(f"Connected to MQTT broker at {BROKER_IP}:{PORT}")
    except Exception as e:
        print(f"Failed to connect to broker: {e}")
        return

    client.loop_start()

    print("Starting 3-Stage Creep Subsidence Simulation...")
    print(f"Target E_max (Failure): {E_max:.4f}")
    
    start_time = time.time()
    
    try:
        while True:
            t = time.time() - start_time
            
            true_strain, stage = get_creep_strain(t)
            
            if true_strain >= E_max:
                print(f"\n[CRITICAL] STRUCTURAL FAILURE REACHED at t={t:.2f}s!")
                print(f"Final Strain: {true_strain:.4f} >= {E_max}")
                print("Simulation holding at failure state (Ctrl+C to exit).")
                true_strain = E_max
            
            n1_pitch, n2_pitch, n1_flex, n2_flex = calculate_sensor_values(true_strain)
            
            n1_pitch += random.gauss(0, TILT_NOISE_STD_DEV)
            n2_pitch += random.gauss(0, TILT_NOISE_STD_DEV)
            n1_flex += random.gauss(0, FLEX_NOISE_STD_DEV)
            n2_flex += random.gauss(0, FLEX_NOISE_STD_DEV)
            
            packet_node1 = {
                "node_id": 1,
                "pitch_angle": round(n1_pitch, 4),
                "roll_angle": round(random.gauss(0, TILT_NOISE_STD_DEV), 4),
                "flex_resistance": round(n1_flex, 2)
            }
            packet_node2 = {
                "node_id": 2,
                "pitch_angle": round(n2_pitch, 4),
                "roll_angle": round(random.gauss(0, TILT_NOISE_STD_DEV), 4),
                "flex_resistance": round(n2_flex, 2)
            }
            
            client.publish(TOPIC, json.dumps(packet_node1))
            client.publish(TOPIC, json.dumps(packet_node2))
            
            if int(t * PUBLISH_RATE_HZ) % int(PUBLISH_RATE_HZ) == 0:
                print(f"t={t:05.1f}s [{stage}] | Strain: {true_strain:.5f} | N1 Pitch: {n1_pitch:05.2f} deg | N1 Flex: {n1_flex:.1f} ohms")
                
            time.sleep(1.0 / PUBLISH_RATE_HZ)
            
    except KeyboardInterrupt:
        print("\nSimulation manually stopped.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()