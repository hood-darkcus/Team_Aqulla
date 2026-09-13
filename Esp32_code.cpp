#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <math.h>

const char *WIFI_SSID = "HOODHLGN";
const char *WIFI_PASSWORD = "password";
const char *MQTT_SERVER = "192.168.xxx";
const int NODE_ID = 2;

const int MPU_ADDR = 0x68;
const int FLEX_PIN = 34;

const float VCC = 3.3;
const float R_DIV = 10000.0;
const float STRAIGHT_RESISTANCE = 10000.0;
const float BEND_RESISTANCE = 45000.0;

WiFiClient espClient;
PubSubClient mqttClient(espClient);

unsigned long lastMsg = 0;

void setup_wifi()
{
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect()
{
  while (!mqttClient.connected())
  {
    Serial.print("Attempting MQTT connection...");
    String clientId = "SIH_Node" + String(NODE_ID) + "_Client-";
    clientId += String(random(0xffff), HEX);

    if (mqttClient.connect(clientId.c_str()))
    {
      Serial.println("connected");
    }
    else
    {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup()
{
  Serial.begin(115200);
  while (!Serial)
  {
    delay(10);
  }

  // Initialize I2C and sensors
  Wire.begin(21, 22);
  delay(100);

  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0x00);
  Wire.endTransmission();

  pinMode(FLEX_PIN, INPUT);
  analogSetAttenuation(ADC_11db);

  setup_wifi();
  mqttClient.setServer(MQTT_SERVER, 1883);
}

void loop()
{
  if (!mqttClient.connected())
  {
    reconnect();
  }
  mqttClient.loop();

  unsigned long now = millis();

  if (now - lastMsg > 100)
  {
    lastMsg = now;

    Wire.beginTransmission(MPU_ADDR);
    Wire.write(0x3B);
    Wire.endTransmission(false);
    Wire.requestFrom((uint8_t)MPU_ADDR, (size_t)14, (bool)true);

    float tiltPitch = 0, tiltRoll = 0;
    if (Wire.available() >= 14)
    {
      int16_t axRaw = (Wire.read() << 8) | Wire.read();
      int16_t ayRaw = (Wire.read() << 8) | Wire.read();
      int16_t azRaw = (Wire.read() << 8) | Wire.read();
      Wire.read();
      Wire.read(); // Skip temp
      int16_t gxRaw = (Wire.read() << 8) | Wire.read();
      int16_t gyRaw = (Wire.read() << 8) | Wire.read();
      int16_t gzRaw = (Wire.read() << 8) | Wire.read();

      float ax = axRaw / 16384.0;
      float ay = ayRaw / 16384.0;
      float az = azRaw / 16384.0;

      tiltPitch = atan2(ay, sqrt(ax * ax + az * az)) * 180.0 / M_PI;
      tiltRoll = atan2(-ax, sqrt(ay * ay + az * az)) * 180.0 / M_PI;
    }

    int adcValue = analogRead(FLEX_PIN);
    float voltage = (float)adcValue * (VCC / 4095.0);
    float flexResistance = 0;
    float bendAngle = 0;
    if (voltage > 0 && voltage < VCC)
    {
      flexResistance = R_DIV * ((VCC / voltage) - 1.0);
      bendAngle = map(flexResistance, STRAIGHT_RESISTANCE, BEND_RESISTANCE, 0, 90);
      bendAngle = constrain(bendAngle, 0, 90);
    }

    JsonDocument doc;
    doc["node_id"] = NODE_ID;                              // Must be integer 1 or 2
    doc["pitch_angle"] = serialized(String(tiltPitch, 2)); // Fixed key
    doc["roll_angle"] = serialized(String(tiltRoll, 2));   // Fixed key
    doc["flex_resistance"] = serialized(String(flexResistance, 1));
    doc["flex_angle"] = serialized(String(bendAngle, 1));

    char jsonBuffer[256];
    serializeJson(doc, jsonBuffer);

    Serial.print("Uploading to MQTT -> Topic: mine/telemetry | Payload: ");
    Serial.println(jsonBuffer);

    mqttClient.publish("mine/telemetry", jsonBuffer);
  }
}
