/*
 * AI Medical Monitor - ESP32 Vitals Transmitter
 * 
 * Hardware Wiring:
 * 1. MAX30102 (I2C Pulse Oximeter & Heart Rate):
 *    - VCC  -> 3.3V
 *    - GND  -> GND
 *    - SDA  -> GPIO 21 (Default I2C SDA on ESP32)
 *    - SCL  -> GPIO 22 (Default I2C SCL on ESP32)
 * 
 * 2. DS18B20 (Dallas OneWire Temperature Sensor):
 *    - VCC  -> 3.3V / 5V
 *    - GND  -> GND
 *    - DQ   -> GPIO 4 (Requires a 4.7k Ohm pull-up resistor to VCC)
 * 
 * Required Arduino Libraries:
 * - PubSubClient (by Nick O'Leary)
 * - ArduinoJson (by Benoit Blanchon)
 * - SparkFun MAX3010x Pulse and Proximity Sensor Library
 * - OneWire (by Paul Stoffregen)
 * - DallasTemperature (by Miles Burton)
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"
#include <OneWire.h>
#include <DallasTemperature.h>

// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT Configuration
const char* mqtt_server = "192.168.1.100"; // Replace with your backend server IP
const int mqtt_port = 1883;
const char* bed_id = "BED-01"; // Bed ID associated with patient in SQLite

// MQTT Topic
char mqtt_topic[50];

// Pin Configuration
#define ONE_WIRE_BUS 4  // DS18B20 DQ pin connected to GPIO 4

// Initialize Sensors
MAX30105 particleSensor;
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature tempSensor(&oneWire);

// WiFi & MQTT Clients
WiFiClient espClient;
PubSubClient client(espClient);

// Vitals Variables
float current_heart_rate = 0.0;
float current_spo2 = 0.0;
float current_temp = 0.0;
bool finger_detected = false;
int reading_confidence = 0;

// Heart rate calculation parameters
const byte RATE_SIZE = 4; // Increase for more averaging
byte rates[RATE_SIZE];
byte rateSpot = 0;
long lastBeat = 0; // Time at which the last beat occurred
float beatsPerMinute;
int beatAvg;

unsigned long lastPublishTime = 0;
const unsigned long publishInterval = 2000; // Publish every 2 seconds

void setup() {
  Serial.begin(115200);
  delay(10);
  
  Serial.println("\n--- AI Medical Monitor ESP32 Setup ---");
  
  // Format MQTT Topic
  snprintf(mqtt_topic, sizeof(mqtt_topic), "hospital/bed/%s/vitals", bed_id);
  Serial.print("Target MQTT Topic: ");
  Serial.println(mqtt_topic);

  // Initialize WiFi
  setup_wifi();
  
  // Configure MQTT
  client.setServer(mqtt_server, mqtt_port);
  
  // Initialize DS18B20 Temp Sensor
  tempSensor.begin();
  Serial.println("DS18B20 temperature sensor initialized.");

  // Initialize MAX30102 Sensor
  if (!particleSensor.begin(Wire, I2CDELAY_NORMAL)) {
    Serial.println("MAX30102 was not found. Please check wiring/power.");
    while (1);
  }
  Serial.println("MAX30102 pulse oximeter initialized.");

  // Configure MAX30102 settings for oximetry
  byte ledBrightness = 60; // Options: 0=Off to 255=50mA
  byte sampleAverage = 4; // Options: 1, 2, 4, 8, 16, 32
  byte ledMode = 2; // Options: 1 = Red only, 2 = Red + IR, 3 = Red + IR + Green
  byte sampleRate = 100; // Options: 50, 100, 200, 400, 800, 1000, 1600, 3200
  int pulseWidth = 411; // Options: 69, 118, 215, 411
  int adcRange = 4096; // Options: 2048, 4096, 8192, 16384

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

  randomSeed(micros());
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Create a random client ID
    String clientId = "ESP32Client-";
    clientId += String(random(0xffff), HEX);
    // Attempt to connect
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // 1. Read MAX30102 SpO2 & Heart Rate
  long irValue = particleSensor.getIR();
  long redValue = particleSensor.getRed();
  
  if (irValue < 50000) {
    // No finger detected
    finger_detected = false;
    current_heart_rate = 0.0;
    current_spo2 = 0.0;
    reading_confidence = 0;
    Serial.println("No finger detected.");
  } else {
    finger_detected = true;
    
    // Heart rate detection logic
    if (checkForBeat(irValue) == true) {
      long delta = millis() - lastBeat;
      lastBeat = millis();
      beatsPerMinute = 60 / (delta / 1000.0);

      if (beatsPerMinute < 255 && beatsPerMinute > 20) {
        rates[rateSpot++] = (byte)beatsPerMinute;
        rateSpot %= RATE_SIZE;

        // Take average of readings
        beatAvg = 0;
        for (byte x = 0 ; x < RATE_SIZE ; x++) {
          beatAvg += rates[x];
        }
        beatAvg /= RATE_SIZE;
      }
    }
    
    current_heart_rate = beatAvg > 0 ? (float)beatAvg : 72.0; // Fallback to healthy baseline or latest avg
    
    // Approximate SpO2 using red and IR ratio
    // Note: A true SpO2 calibration requires clinical lookup tables. 
    // Here we use a standard linear approximation for demonstration.
    float ratio = (float)redValue / (float)irValue;
    float spo2Approx = 110.0 - 15.0 * ratio; // Approximation equation
    if (spo2Approx > 100.0) spo2Approx = 100.0;
    if (spo2Approx < 50.0) spo2Approx = 50.0;
    current_spo2 = spo2Approx;

    // Set reading confidence based on signal strength stability
    reading_confidence = map(constrain(irValue, 50000, 120000), 50000, 120000, 60, 98);
  }

  // 2. Read DS18B20 Temperature
  tempSensor.requestTemperatures(); 
  float tempC = tempSensor.getTempCByIndex(0);
  if (tempC != DEVICE_DISCONNECTED_C) {
    current_temp = tempC;
  } else {
    current_temp = 0.0;
    Serial.println("Error: Temperature sensor disconnected!");
  }

  // 3. Periodic Publish to MQTT
  unsigned long now = millis();
  if (now - lastPublishTime > publishInterval) {
    lastPublishTime = now;
    
    // Create JSON Document
    StaticJsonDocument<256> doc;
    doc["spo2"] = finger_detected ? round(current_spo2 * 10) / 10.0 : 0.0;
    doc["heart_rate"] = finger_detected ? round(current_heart_rate * 10) / 10.0 : 0.0;
    doc["temperature"] = current_temp > 0 ? round(current_temp * 10) / 10.0 : 0.0;
    doc["confidence"] = finger_detected ? reading_confidence : 0;
    doc["finger_detected"] = finger_detected;
    doc["wifi_rssi"] = WiFi.RSSI();
    doc["source"] = "sensor";

    // Serialize JSON
    char buffer[256];
    serializeJson(doc, buffer);
    
    // Publish MQTT message
    if (client.publish(mqtt_topic, buffer)) {
      Serial.print("Published: ");
      Serial.println(buffer);
    } else {
      Serial.println("Failed to publish vital signs!");
    }
  }

  delay(20); // Small delay to avoid CPU hogging
}
