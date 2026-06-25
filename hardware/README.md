# ESP32 Vitals Monitor Integration

This directory contains the ESP32 microcontroller code (`esp32_monitor.ino`) to read vital signs from physical hardware sensors and stream them to the **AI Medical Monitor** system in real-time.

---

## 🔌 Hardware Wiring Diagram

### 1. MAX30102 (Pulse Oximeter & Heart Rate)
* **Interface**: I2C
* **Connections**:
  | MAX30102 Pin | ESP32 Pin | Description |
  |--------------|-----------|-------------|
  | **VCC**      | `3.3V`    | Power Supply (3.3V) |
  | **GND**      | `GND`     | Ground |
  | **SDA**      | `GPIO 21` | I2C Data Line |
  | **SCL**      | `GPIO 22` | I2C Clock Line |

### 2. DS18B20 (Waterproof Temperature Probe)
* **Interface**: OneWire Digital Protocol
* **Connections** (requires a **4.7kΩ pull-up resistor** between `VCC` and `DQ`):
  | DS18B20 Wire | ESP32 Pin | Description |
  |--------------|-----------|-------------|
  | **Red (VCC)**| `3.3V / 5V`| Power Supply |
  | **Black (GND)**| `GND`   | Ground |
  | **Yellow (DQ)**| `GPIO 4`| OneWire Data Line |

---

## 📚 Software Dependencies

Install the following libraries using the **Arduino Library Manager** (Sketch -> Include Library -> Manage Libraries):
1. **PubSubClient** (by Nick O'Leary) - For MQTT connection.
2. **ArduinoJson** (by Benoit Blanchon) - For parsing and building JSON payloads.
3. **SparkFun MAX3010x Pulse and Proximity Sensor Library** - Drivers for oximetry.
4. **OneWire** (by Paul Stoffregen) - Protocol driver for DS18B20.
5. **DallasTemperature** (by Miles Burton) - Dallas temperature read functions.

---

## ⚙️ Configuration Setup

Open the `esp32_monitor.ino` file and update the following settings to match your network:

```cpp
// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";          // Your local WiFi Name
const char* password = "YOUR_WIFI_PASSWORD";  // Your local WiFi Password

// MQTT Configuration
const char* mqtt_server = "192.168.1.100";    // The IP address of the FastAPI / MQTT host server
const int mqtt_port = 1883;                   // Default MQTT port
const char* bed_id = "BED-01";                // The Bed ID (Must match the Bed ID registered in the application)
```

---

## 🧠 How Sensor Data Enters the AI Analysis

To ensure data from the physical sensors is integrated into the AI's clinical diagnosis, the system implements the following automated pipeline:

1. **Publish**: The ESP32 collects SpO2, heart rate, and temperature, then publishes them to the MQTT topic: `hospital/bed/BED-01/vitals`.
2. **Intercept**: The backend's `MQTTSubscriber` daemon listens to this stream:
   * It extracts the `bed_id` (`BED-01`) from the topic.
   * It queries the relational SQLite database to check which **active patient** is currently admitted to that bed.
3. **Persist**: If a patient is assigned to the bed, the subscriber saves the readings (`spo2`, `heart_rate`, `temperature`) directly into the SQLite `VitalReading` database table.
4. **AI Integration**: When a doctor starts an AI Diagnosis Session or chats with the assistant, the `DiagnosisEngine` executes `gather_context(patient_id)` before calling the LLM:
   * It fetches the patient's latest vital readings (averages, minimums, maximums, and ranges from the last hour).
   * It appends this data directly into the AI system's clinical context.
   * The AI uses these real-time values to identify critical alarms, propose differential diagnoses, or adjust follow-up clinical questions dynamically.
