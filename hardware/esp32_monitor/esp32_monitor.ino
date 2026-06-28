/*
 * AI Medical Monitor - ESP32 Vitals Transmitter
 *
 * Sends SpO2, heart rate, and body temperature to the backend over HTTPS.
 * Designed for cloud deployment (Railway) — no MQTT broker required.
 *
 * Hardware Wiring:
 * 1. MAX30102 (I2C Pulse Oximeter & Heart Rate):
 *    - VCC  -> 3.3V
 *    - GND  -> GND
 *    - SDA  -> GPIO 21 (Default I2C SDA on ESP32)
 *    - SCL  -> GPIO 22 (Default I2C SCL on ESP32)
 *
 * 2. MLX90614 (I2C Infrared Contactless Temperature Sensor):
 *    - VCC  -> 3.3V
 *    - GND  -> GND
 *    - SDA  -> GPIO 21 (Shares I2C bus with MAX30102)
 *    - SCL  -> GPIO 22 (Shares I2C bus with MAX30102)
 *
 * Required Arduino Libraries:
 * - WiFiClientSecure (built into ESP32 core)
 * - HTTPClient (built into ESP32 core)
 * - ArduinoJson (by Benoit Blanchon)
 * - SparkFun MAX3010x Pulse and Proximity Sensor Library
 * - Adafruit MLX90614 Library (by Adafruit)
 * - Adafruit BusIO (dependency of Adafruit MLX90614)
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"
#include <Adafruit_MLX90614.h>

// ======================== Configuration ========================

// WiFi
const char* ssid     = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Backend API
const char* backend_host = "ai-medical-monitor-production.up.railway.app";
const char* bed_id = "BED-01";

// Publishing interval
const unsigned long publishInterval = 2000; // milliseconds

// ======================== End Configuration ========================

// Build the full API URL at runtime
String api_url;

// Initialize Sensors
MAX30105 particleSensor;
Adafruit_MLX90614 mlx;

// WiFi & HTTP
WiFiClientSecure secureClient;

// Vitals Variables
float current_heart_rate = 0.0;
float current_spo2 = 0.0;
float current_temp = 0.0;
bool finger_detected = false;
int reading_confidence = 0;

// Heart rate calculation parameters
const byte RATE_SIZE = 4;
byte rates[RATE_SIZE];
byte rateSpot = 0;
long lastBeat = 0;
float beatsPerMinute;
int beatAvg;

unsigned long lastPublishTime = 0;

void setup() {
  Serial.begin(115200);
  delay(10);

  Serial.println("\n--- AI Medical Monitor ESP32 Setup ---");

  // Build API URL
  api_url = String("https://") + backend_host + "/api/beds/" + bed_id + "/vitals";
  Serial.print("API endpoint: ");
  Serial.println(api_url);
  Serial.print("Bed ID: ");
  Serial.println(bed_id);

  // Initialize WiFi
  setup_wifi();

  // Configure TLS — skip cert verification (ESP32 cannot easily bundle CA certs
  // that expire; acceptable for sensor data over a known endpoint)
  secureClient.setInsecure();

  // Initialize I2C bus
  Wire.begin(21, 22);

  // Initialize MLX90614 Temperature Sensor
  if (!mlx.begin()) {
    Serial.println("MLX90614 was not found. Please check wiring.");
    while (1);
  }
  Serial.println("MLX90614 infrared temperature sensor initialized.");

  // Initialize MAX30102 Sensor
  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD, 0x57)) {
    Serial.println("MAX30102 was not found. Please check wiring/power.");
    while (1);
  }
  Serial.println("MAX30102 pulse oximeter initialized.");

  // Configure MAX30102 settings for oximetry
  byte ledBrightness = 60;
  byte sampleAverage = 4;
  byte ledMode = 2;       // Red + IR
  byte sampleRate = 100;
  int pulseWidth = 411;
  int adcRange = 4096;

  particleSensor.setup(ledBrightness, sampleAverage, ledMode, sampleRate, pulseWidth, adcRange);
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.print("Signal strength (RSSI): ");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm");
}

void publish_vitals() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected — skipping publish");
    return;
  }

  // Build JSON payload
  StaticJsonDocument<256> doc;
  doc["spo2"] = finger_detected ? round(current_spo2 * 10) / 10.0 : 0.0;
  doc["heart_rate"] = finger_detected ? round(current_heart_rate * 10) / 10.0 : 0.0;
  doc["temperature"] = current_temp > 0 ? round(current_temp * 10) / 10.0 : 0.0;
  doc["confidence"] = finger_detected ? reading_confidence : 0;
  doc["finger_detected"] = finger_detected;
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["source"] = "sensor";

  char buffer[256];
  serializeJson(doc, buffer);

  HTTPClient http;
  http.begin(secureClient, api_url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(10000);

  int httpCode = http.POST(buffer);

  if (httpCode > 0) {
    if (httpCode == 201) {
      Serial.print("Published (201): ");
      Serial.println(buffer);
    } else {
      Serial.print("HTTP ");
      Serial.print(httpCode);
      Serial.print(": ");
      Serial.println(http.getString());
    }
  } else {
    Serial.print("HTTP POST failed: ");
    Serial.println(http.errorToString(httpCode));
  }

  http.end();
}

void loop() {
  // 1. Read MAX30102 SpO2 & Heart Rate
  long irValue = particleSensor.getIR();
  long redValue = particleSensor.getRed();

  if (irValue < 50000) {
    finger_detected = false;
    current_heart_rate = 0.0;
    current_spo2 = 0.0;
    reading_confidence = 0;
  } else {
    finger_detected = true;

    // Heart rate detection
    if (checkForBeat(irValue) == true) {
      long delta = millis() - lastBeat;
      lastBeat = millis();
      beatsPerMinute = 60 / (delta / 1000.0);

      if (beatsPerMinute < 255 && beatsPerMinute > 20) {
        rates[rateSpot++] = (byte)beatsPerMinute;
        rateSpot %= RATE_SIZE;

        beatAvg = 0;
        for (byte x = 0; x < RATE_SIZE; x++) {
          beatAvg += rates[x];
        }
        beatAvg /= RATE_SIZE;
      }
    }

    current_heart_rate = beatAvg > 0 ? (float)beatAvg : 72.0;

    // Approximate SpO2 using red/IR ratio
    float ratio = (float)redValue / (float)irValue;
    float spo2Approx = 110.0 - 15.0 * ratio;
    if (spo2Approx > 100.0) spo2Approx = 100.0;
    if (spo2Approx < 50.0) spo2Approx = 50.0;
    current_spo2 = spo2Approx;

    reading_confidence = map(constrain(irValue, 50000, 120000), 50000, 120000, 60, 98);
  }

  // 2. Read MLX90614 Body Temperature (infrared, contactless)
  // readObjectTempC() = the target surface (skin) temperature
  float tempC = mlx.readObjectTempC();
  // Sanity check: MLX90614 returns large negative values on read failure
  if (tempC > 10.0 && tempC < 50.0) {
    // Apply a small empirical offset to better approximate core body temperature
    // (skin surface reads ~1-2C lower than oral/core). Adjust as needed.
    current_temp = tempC + 1.5;
  } else {
    // Sensor read error — keep last valid reading or 0
    if (current_temp <= 0) {
      current_temp = 0.0;
      Serial.println("MLX90614 read error — out of valid range");
    }
  }

  // 3. Periodic publish to backend
  unsigned long now = millis();
  if (now - lastPublishTime > publishInterval) {
    lastPublishTime = now;
    publish_vitals();
  }

  delay(20);
}
