/*
  GSMClient with OLED Display, PIR Sensor, BME688, and API Data Posting

  This sketch connects to a website using the Portenta CAT.M1/NB IoT GNSS Shield.
  Displays info on OLED, PIR sensor status, BME688 readings, and posts data to API.
*/

#include <Arduino_PortentaBreakout.h>
#include <GSM.h>
#include <Arduino_DebugUtils.h>
#include <GSMDebug.h>
#include "arduino_secrets.h"

// OLED display libs
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// BME688 atmospheric sensor libs
#include <Adafruit_Sensor.h>
#include <Adafruit_BME680.h>

// OLED setup
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C
const uint8_t LINE_HEIGHT = 8;

// PIR sensor setup
#define PIR_PIN GPIO_0

// BME688 setup - using I2C1
#define BME688_I2C_ADDR 0x77

// API configuration
#define API_SERVER "167.99.39.10"
#define API_PORT 8000
#define API_PATH "/api/v1/sensors/data/"
#define STATION_ID "mombarone-san-carlo"
#define POST_INTERVAL 60000  // == 1 minute

// Location configuration
#define LATITUDE 45.5615
#define LONGITUDE 8.0573
#define ALTITUDE 1250
#define TRAIL_NAME "Sentiero Graglia"

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
Adafruit_BME680 bme(&Wire1);

char pin[]      = SECRET_PIN;
char apn[]      = SECRET_APN;
char username[] = SECRET_USERNAME;
char pass[]     = SECRET_PASSWORD;

GSMClient client;

// ------------ Parsed network info ------------
String g_rat = "";
long   g_cid = -1;
int    g_rssi = 0;
int    g_retry = -1;
String g_status = "Init...";  // Current connection status
bool g_pir_state = false;      // PIR sensor state
bool g_pir_last_state = false; // Previous PIR state for edge detection
uint8_t g_pir_count = 0;       // PIR event counter (max 99)
uint8_t g_pir_count_last_post = 0;  // PIR count at last API post

// BME688 data
float g_temperature = 0.0;
float g_humidity = 0.0;
float g_pressure = 0.0;
bool g_bme_available = false;

// Timing
unsigned long g_last_api_post = 0;
bool g_first_post_done = false;

// Forward declarations
void updateRSSI(int rssi);
void updateRAT(const String &rat);
void updateCID(long cid);
void updateRetry(int retry);
void updateStatus(const String &status);
void updateOLED();
void updatePIR();
void updateBME688();
void sendDataToAPI();
String getISO8601Timestamp();

// OLED print function
void printLine(uint8_t line, const char* text) {
  if (line > 3) return;
  
  uint8_t y = line * LINE_HEIGHT;
  display.fillRect(0, y, SCREEN_WIDTH, LINE_HEIGHT, SSD1306_BLACK);
  display.setCursor(0, y);
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.print(text);
  display.display();
}

// Draw PIR indicator with counter and BME688 data on line 3
void drawPIRIndicator(bool motion_detected, uint8_t count) {
  uint8_t y = 3 * LINE_HEIGHT;
  uint8_t centerX = 4;  // Left side of line 3
  uint8_t centerY = y + 4;  // Center vertically in the line
  uint8_t radius = 3;
  
  // Clear the line first
  display.fillRect(0, y, SCREEN_WIDTH, LINE_HEIGHT, SSD1306_BLACK);
  
  if (motion_detected) {
    // Filled circle for motion detected (HIGH)
    display.fillCircle(centerX, centerY, radius, SSD1306_WHITE);
  } else {
    // Empty circle for no motion (LOW)
    display.drawCircle(centerX, centerY, radius, SSD1306_WHITE);
  }
  
  // Draw counter next to circle (limit to 99)
  display.setCursor(10, y);
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  if (count > 99) count = 99;
  if (count < 10) {
    display.print("0");
  }
  display.print(count);
  
  // Draw BME688 data after counter with units
  if (g_bme_available) {
    char bme_str[20];
    snprintf(bme_str, sizeof(bme_str), " %2dC %2d%% %4dhPa", 
             (int)g_temperature, 
             (int)g_humidity, 
             (int)g_pressure);
    display.setCursor(25, y);
    display.print(bme_str);
  } else {
    display.setCursor(25, y);
    display.print(" --C --% --hPa");
  }
  
  display.display();
}

// Generate ISO8601 timestamp (simplified - uses millis as time reference)
String getISO8601Timestamp() {
  // For a real timestamp, you'd need to get time from GSM network or NTP
  // This is not used now: overriden on the server
  unsigned long seconds = millis() / 1000;
  unsigned long minutes = seconds / 60;
  unsigned long hours = minutes / 60;
  
  char timestamp[25];
  snprintf(timestamp, sizeof(timestamp), "2025-11-22T%02lu:%02lu:%02luZ", 
           hours % 24, minutes % 60, seconds % 60);
  return String(timestamp);
}

// Send data to API
void sendDataToAPI() {
  Serial.println("Attempting to send data to API...");
  Serial.print("Connecting to ");
  Serial.print(API_SERVER);
  Serial.print(":");
  Serial.println(API_PORT);
  
  // Calculate motion count since last post
  uint8_t motion_count = g_pir_count - g_pir_count_last_post;
  if (g_pir_count < g_pir_count_last_post) {
    // Handle counter overflow/reset
    motion_count = g_pir_count;
  }
  
  // Build JSON payload
  String jsonData = "{";
  jsonData += "\"station_id\":\"" + String(STATION_ID) + "\",";
  jsonData += "\"timestamp\":\"" + getISO8601Timestamp() + "\",";
  jsonData += "\"location\":{";
  jsonData += "\"latitude\":" + String(LATITUDE, 4) + ",";
  jsonData += "\"longitude\":" + String(LONGITUDE, 4) + ",";
  jsonData += "\"altitude\":" + String(ALTITUDE) + ",";
  jsonData += "\"trail_name\":\"" + String(TRAIL_NAME) + "\"";
  jsonData += "},";
  jsonData += "\"sensors\":{";
  
  // Atmospheric data
  jsonData += "\"atmospheric\":{";
  if (g_bme_available) {
    jsonData += "\"temperature\":" + String(g_temperature, 1) + ",";
    jsonData += "\"humidity\":" + String(g_humidity, 1) + ",";
    jsonData += "\"pressure\":" + String(g_pressure, 1);
  } else {
    jsonData += "\"temperature\":null,";
    jsonData += "\"humidity\":null,";
    jsonData += "\"pressure\":null";
  }
  jsonData += "},";
  
  // Light data (placeholder - add actual sensors if available)
  jsonData += "\"light\":{";
  jsonData += "\"uv_index\":null,";
  jsonData += "\"lux\":null";
  jsonData += "},";
  
  // Soil data (placeholder)
  jsonData += "\"soil\":{";
  jsonData += "\"moisture_percent\":null";
  jsonData += "},";
  
  // Air quality (placeholder)
  jsonData += "\"air_quality\":{";
  jsonData += "\"co2_ppm\":null";
  jsonData += "},";
  
  // Precipitation (placeholder)
  jsonData += "\"precipitation\":{";
  jsonData += "\"is_raining\":false,";
  jsonData += "\"rain_detected_last_hour\":false";
  jsonData += "},";
  
  // Trail activity
  jsonData += "\"trail_activity\":{";
  jsonData += "\"motion_count\":" + String(motion_count) + ",";
  jsonData += "\"period_minutes\":" + String(POST_INTERVAL / 60000);
  jsonData += "}";
  
  jsonData += "}}";
  
  Serial.println("JSON payload:");
  Serial.println(jsonData);
  Serial.print("Payload size: ");
  Serial.print(jsonData.length());
  Serial.println(" bytes");
  
  // Check if client is already connected
  if (client.connected()) {
    Serial.println("Client already connected, stopping...");
    client.stop();
    delay(1000);
  }
  
  Serial.println("Attempting connection...");
  
  // Connect to API server
  int connectResult = client.connect(API_SERVER, API_PORT);
  
  Serial.print("Connection result: ");
  Serial.println(connectResult);
  
  if (connectResult == 1) {
    Serial.println("Connected to API server successfully!");
    
    // Send POST request
    client.println("POST " + String(API_PATH) + " HTTP/1.1");
    client.println("Host: " + String(API_SERVER));
    client.println("Content-Type: application/json");
    client.print("Content-Length: ");
    client.println(jsonData.length());
    client.println("Connection: close");
    client.println();
    client.println(jsonData);
    
    Serial.println("POST request sent, waiting for response...");
    
    // Wait for response
    unsigned long timeout = millis();
    bool gotResponse = false;
    while (client.connected() && millis() - timeout < 10000) {
      if (client.available()) {
        gotResponse = true;
        char c = client.read();
        Serial.write(c);
      }
    }
    
    if (!gotResponse) {
      Serial.println("\nNo response received from server");
    }
    
    client.stop();
    Serial.println("\nAPI request completed");
    
    // Update counter
    g_pir_count_last_post = g_pir_count;
    
  } else {
    Serial.print("Failed to connect to API server. Error code: ");
    Serial.println(connectResult);
    Serial.println("Possible reasons:");
    Serial.println("- Server is down or unreachable");
    Serial.println("- Network connectivity issues");
    Serial.println("- Incorrect IP address or port");
    Serial.println("- Firewall blocking the connection");
    
    // Additional diagnostics
    Serial.print("Signal strength (RSSI): ");
    Serial.println(g_rssi);
  }
}

void testConnection() {
  Serial.println("Testing connection to Google DNS (8.8.8.8:53)...");
  
  if (client.connect("8.8.8.8", 53)) {
    Serial.println("SUCCESS: Connected to 8.8.8.8");
    client.stop();
  } else {
    Serial.println("FAILED: Could not connect to 8.8.8.8");
  }
  
  delay(2000);
  
  Serial.println("Testing connection to API server IP...");
  if (client.connect("167.99.39.10", 8000)) {
    Serial.println("SUCCESS: Connected to API server");
    client.stop();
  } else {
    Serial.println("FAILED: Could not connect to API server");
  }
}

// Update PIR sensor - called frequently from loop
void updatePIR() {
  // Read current PIR state
  int reading = digitalRead(PIR_PIN);
  g_pir_state = (reading == HIGH);
  
  // Detect rising edge (LOW to HIGH transition) = new event
  if (g_pir_state && !g_pir_last_state) {
    g_pir_count++;
    if (g_pir_count > 99) g_pir_count = 0;  // Reset at 100
    Serial.print("PIR Event detected! Count: ");
    Serial.println(g_pir_count);
    drawPIRIndicator(g_pir_state, g_pir_count);
  }
  // Detect falling edge (HIGH to LOW)
  else if (!g_pir_state && g_pir_last_state) {
    Serial.println("PIR motion ended");
    drawPIRIndicator(g_pir_state, g_pir_count);
  }
  
  g_pir_last_state = g_pir_state;
}

// Update BME688 readings
void updateBME688() {
  if (!g_bme_available) return;
  
  if (bme.performReading()) {
    g_temperature = bme.temperature;
    g_humidity = bme.humidity;
    g_pressure = bme.pressure / 100.0;  // Convert Pa to hPa
    
    Serial.print("Temperature: ");
    Serial.print(g_temperature);
    Serial.print(" °C, Humidity: ");
    Serial.print(g_humidity);
    Serial.print(" %, Pressure: ");
    Serial.print(g_pressure);
    Serial.println(" hPa");
    
    drawPIRIndicator(g_pir_state, g_pir_count);
    
    // Send first post after first successful BME reading
    if (!g_first_post_done) {
      g_first_post_done = true;
      g_last_api_post = millis();
      sendDataToAPI();
    }
  } else {
    Serial.println("BME688 reading failed");
  }
}

// ------------ Debug listener ------------
class DebugListener : public Stream {
public:
  Stream* target;
  String buffer;

  DebugListener(Stream* forwardTo) : target(forwardTo), buffer("") {}

  virtual size_t write(uint8_t c) override {
    if (target) target->write(c);

    if (c == '\n') {
      processLine(buffer);
      buffer = "";
    } else if (c != '\r') {
      buffer += (char)c;
    }

    return 1;
  }

  virtual int available() override { return 0; }
  virtual int read() override { return -1; }
  virtual int peek() override { return -1; }
  virtual void flush() override {}

  void processLine(const String &line) {
    // Look for "RSSI: -79"
    int pos = line.indexOf("RSSI:");
    if (pos >= 0) {
      String v = line.substring(pos + 5);
      v.trim();
      updateRSSI(v.toInt());
    }

    // Look for "RAT changed: NB1"
    pos = line.indexOf("RAT changed:");
    if (pos >= 0) {
      int colon = line.indexOf(':', pos);
      if (colon >= 0) {
        String rat = line.substring(colon + 1);
        rat.trim();
        updateRAT(rat);
      }
    }

    // Look for "Cellular ID changed: 3894897"
    pos = line.indexOf("Cellular ID changed:");
    if (pos >= 0) {
      int colon = line.indexOf(':', pos);
      if (colon >= 0) {
        String cidStr = line.substring(colon + 1);
        cidStr.trim();
        updateCID(cidStr.toInt());
      }
    }

    // Look for "retry count 9"
    pos = line.indexOf("retry count");
    if (pos >= 0) {
      int lastSpace = line.lastIndexOf(' ');
      if (lastSpace >= 0 && lastSpace + 1 < (int)line.length()) {
        String retryStr = line.substring(lastSpace + 1);
        retryStr.trim();
        int retryVal = retryStr.toInt();
        if (retryVal >= 0) {
          updateRetry(retryVal);
        }
      }
    }

    pos = line.indexOf(" Searching Network");
    if (pos >= 0) {
      updateStatus("Searching...");
    }

    pos = line.indexOf(" Registration Denied");
    if (pos >= 0) {
      updateStatus("Reg Denied");
    }
  }
};

// Global listener instance
DebugListener debugListener(&Serial);

// ------------ Helpers for OLED + state ------------
void updateRSSI(int rssi) {
  g_rssi = rssi;
  updateOLED();
}

void updateRAT(const String &rat) {
  g_rat = rat;
  updateOLED();
}

void updateCID(long cid) {
  g_cid = cid;
  updateOLED();
}

void updateRetry(int retry) {
  g_retry = retry;
  updateOLED();
}

void updateStatus(const String &status) {
  g_status = status;
  updateOLED();
}

void updateOLED() {
  char line[22];
  
  // Line 0: Status
  snprintf(line, sizeof(line), "Status: %s", g_status.c_str());
  printLine(0, line);
  
  // Line 1: RSSI
  if (g_rssi != 0) {
    snprintf(line, sizeof(line), "RSSI: %d dBm", g_rssi);
  } else {
    snprintf(line, sizeof(line), "RSSI: --");
  }
  printLine(1, line);
  
  // Line 2: RAT and CID (if connected) OR Retry count (if connecting)
  if (g_rat.length() > 0 && g_cid >= 0) {
    // Connected - show RAT and CID
    snprintf(line, sizeof(line), "RAT:%s CID:%ld", g_rat.c_str(), g_cid);
  } else if (g_retry >= 0) {
    // Still connecting - show retry count
    snprintf(line, sizeof(line), "Retry: %d", g_retry);
  } else {
    // No data yet
    snprintf(line, sizeof(line), "RAT: --");
  }
  printLine(2, line);
  
  // Line 3: PIR indicator with counter and BME688 data (drawn separately)
  drawPIRIndicator(g_pir_state, g_pir_count);
}

void setup() {
  Serial.begin(9600);
  
  // Initialize PIR sensor first
  pinMode(PIR_PIN, INPUT_PULLDOWN);
  Serial.println("PIR sensor initialized on GPIO_0 with pulldown");
  
  // Initialize I2C1 for BME688
  Wire1.begin();
  Serial.println("I2C1 initialized for BME688");
  
  // Initialize BME688
  if (bme.begin(BME688_I2C_ADDR, true)) {  // true = use Wire1
    Serial.println("BME688 sensor found!");
    g_bme_available = true;
    
    // Set up oversampling and filter initialization
    bme.setTemperatureOversampling(BME680_OS_8X);
    bme.setHumidityOversampling(BME680_OS_2X);
    bme.setPressureOversampling(BME680_OS_4X);
    bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
    bme.setGasHeater(320, 150); // 320*C for 150 ms
  } else {
    Serial.println("BME688 sensor not found! Check wiring and I2C address");
    g_bme_available = false;
  }
  
  // Initialize OLED on I2C0 (Wire)
  display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS, false);
  display.clearDisplay();
  display.display();

  // Initialize OLED with startup message
  updateStatus("Init...");
  
  // Show initial PIR state
  drawPIRIndicator(false, 0);

#if defined(ARDUINO_EDGE_CONTROL)
  pinMode(ON_MKR2, OUTPUT);
  digitalWrite(ON_MKR2, HIGH);
#endif

  Debug.setDebugOutputStream(&debugListener);
  Debug.setDebugLevel(DBG_VERBOSE);

  Serial.println("Starting Carrier Network registration");
  
  updateStatus("Registering");
  
  bool ok = GSM.begin(pin, apn, username, pass, CATNB, BAND_8 | BAND_20);
  
  if (!ok) {
    Serial.println("GSM registration failed");
    updateStatus("Reg Failed");
    // Continue running even if GSM fails - PIR and BME688 will still work
  } else {
    Serial.println("GSM registration successful");
    updateStatus("Registered");
    testConnection(); 
  }
}

void loop() {
  static unsigned long lastBMERead = 0;
  const unsigned long BME_INTERVAL = 10000;  // Read BME688 every 2 seconds
  
  // ALWAYS update PIR sensor - independent of network status
  updatePIR();
  
  // Update BME688 periodically
  unsigned long currentMillis = millis();
  if (currentMillis - lastBMERead >= BME_INTERVAL) {
    lastBMERead = currentMillis;
    updateBME688();
  }
  
  // Send data to API every POST_INTERVAL (60 seconds)
  if (g_first_post_done && (currentMillis - g_last_api_post >= POST_INTERVAL)) {
    g_last_api_post = currentMillis;
    sendDataToAPI();
  }
  
  // Small delay to prevent excessive polling
  delay(50);
}