import paho.mqtt.client as mqtt
import time

def on_message(client, userdata, msg):
    print(f"Topic: {msg.topic}, Payload: {msg.payload}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.on_message = on_message
client.connect("localhost")
client.subscribe("#")
client.loop_start()

print("Listening for 10 seconds...")
time.sleep(10)
client.loop_stop()
print("Done.")
