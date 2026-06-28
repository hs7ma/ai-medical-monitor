# ESP32 Vitals Monitor Integration

This directory contains the ESP32 microcontroller code (`esp32_monitor.ino`) to read vital signs from physical hardware sensors and stream them to the **AI Medical Monitor** backend over HTTPS.

No MQTT broker is required — the ESP32 sends readings directly to the backend API, making it compatible with cloud deployments (e.g. Railway).

---

## Hardware Wiring Diagram

### 1. MAX30102 (Pulse Oximeter & Heart Rate)
* **Interface**: I2C
* **Connections**:
  | MAX30102 Pin | ESP32 Pin | Description |
  |--------------|-----------|-------------|
  | **VCC**      | `3.3V`    | Power Supply (3.3V) |
  | **GND**      | `GND`     | Ground |
  | **SDA**      | `GPIO 21` | I2C Data Line |
  | **SCL**      | `GPIO 22` | I2C Clock Line |

### 2. MLX90614 (Infrared Contactless Temperature Sensor)
* **Interface**: I2C (shares the same bus as MAX30102)
* **Connections**:
  | MLX90614 Pin | ESP32 Pin | Description |
  |--------------|-----------|-------------|
  | **VCC**      | `3.3V`    | Power Supply (3.3V) |
  | **GND**      | `GND`     | Ground |
  | **SDA**      | `GPIO 21` | I2C Data Line (shared) |
  | **SCL**      | `GPIO 22` | I2C Clock Line (shared) |

> The MLX90614 measures skin surface temperature contactlessly via infrared. A small empirical offset (+1.5 C) is applied in firmware to approximate core body temperature. Adjust this offset in the code if you calibrate against a clinical reference.

---

## Software Dependencies

Install the following libraries using the **Arduino Library Manager** (Sketch -> Include Library -> Manage Libraries):
1. **ArduinoJson** (by Benoit Blanchon) - For building JSON payloads.
2. **SparkFun MAX3010x Pulse and Proximity Sensor Library** - Drivers for oximetry.
3. **Adafruit MLX90614 Library** (by Adafruit) - Driver for the infrared temperature sensor.
4. **Adafruit BusIO** - Required dependency for Adafruit MLX90614.

> `WiFiClientSecure` and `HTTPClient` are built into the ESP32 Arduino core — no additional installation needed.

---

## Configuration Setup

Open the `esp32_monitor.ino` file and update the following settings to match your network and deployment:

```cpp
// WiFi
const char* ssid     = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Backend API
const char* backend_host = "ai-medical-monitor-production.up.railway.app";
const char* bed_id       = "BED-01";
```

### Where to find the values
* **backend_host**: The hostname of your deployed backend (without `https://`). For local development, use your computer's LAN IP (e.g. `192.168.1.100`) and change the URL scheme from HTTPS to HTTP in the code.
* **bed_id**: Must match a Bed ID registered in the application, and a patient must be assigned to that bed for readings to be saved.

---

## How Sensor Data Enters the AI Analysis

1. **Read**: The ESP32 collects SpO2 and heart rate from the MAX30102, and body temperature from the MLX90614.
2. **Transmit**: Every 2 seconds, the ESP32 sends an HTTPS POST to `/api/beds/{bed_id}/vitals` with the vital signs JSON payload.
3. **Persist**: The backend looks up which patient is assigned to the bed, then saves the reading into the SQLite `VitalReading` table and InfluxDB time-series.
4. **Broadcast**: The reading is pushed to connected frontend clients via WebSocket for live dashboard updates.
5. **AI Integration**: When a doctor starts an AI Diagnosis Session, the `DiagnosisEngine` fetches the patient's latest vital readings and includes them in the clinical context sent to the LLM. The AI uses these real-time values to propose diagnoses and adjust follow-up questions.
