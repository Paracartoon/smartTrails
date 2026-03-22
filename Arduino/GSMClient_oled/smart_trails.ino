/*
  Trail Weather Station — Portenta H7 + CAT.M1/NB-IoT GNSS Shield

  Reads environmental sensors (BME688, DS18B20, LTR390, VEML7700, ENS160,
  AHT21, capacitive soil moisture, rain detector) and a PIR motion sensor,
  displays a summary on a 128x32 OLED, and posts JSON data to a remote API
  every 15 minutes over NB-IoT / CAT-M1.

  Between sends the modem is powered off to conserve energy.
*/

// --- Core / GSM ---
#include <GSM.h>
#include <MbedUdp.h>
#include <SocketHelpers.h>
#include <Arduino_DebugUtils.h>
#include <GSMDebug.h>
#include "arduino_secrets.h"

// --- Time ---
#include <NTPClient.h>

// --- Flash storage ---
#include <FlashIAPBlockDevice.h>

// --- Display ---
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// --- Environmental sensors ---
#include <Adafruit_Sensor.h>
#include <Adafruit_BME680.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "Adafruit_LTR390.h"
#include "Adafruit_VEML7700.h"
#include "SparkFun_ENS160.h"
#include <Adafruit_AHTX0.h>

// --- Power management ---
#include <Arduino_PowerManagement.h>

// ============================================================================
// PIN DEFINITIONS
// ============================================================================

#define PIR_PIN          D7   // AM312 PIR sensor, polled in loop()
#define OLED_POWER_PIN   D2   // 2N3904 MOSFET gate: HIGH = OLED on
#define BUTTON_PIN       D3   // Active LOW, pressed = GND
#define DS18B20_PIN      D5   // DS18B20 OneWire soil temperature sensor
#define SOIL_MOISTURE_PIN A3  // DFRobot capacitive soil moisture (analog)
#define RAIN_SENSOR_PIN   A4  // Electrode to GND, pullup: LOW = rain

// Calibrated soil moisture thresholds (adjust per sensor)
#define SOIL_MOISTURE_DRY 790
#define SOIL_MOISTURE_WET 480

// BME688 I2C address (0x77 default, 0x76 if SDO pulled low)
#define BME688_I2C_ADDR 0x77

// Modem hardware control pins
#define MODEM_FST_SHDN_PIN   PK_1
#define MODEM_ON_3V3_PIN     PH_15
#define MODEM_EMERG_RST_PIN  PJ_7
#define MODEM_PSM_WAKEUP_PIN PJ_10
#define MODEM_RTS_PIN        PI_10

// OLED geometry
#define SCREEN_WIDTH   128
#define SCREEN_HEIGHT  32
#define OLED_RESET     -1
#define SCREEN_ADDRESS 0x3C
const uint8_t LINE_HEIGHT = 8;

// ============================================================================
// CONFIGURATION
// ============================================================================

// Per-deployment settings (edit these files to change)
#include "api_config.h"
#include "station_config.h"

#define POST_INTERVAL          900000UL  // 15 min between API posts
#define SENSOR_READ_INTERVAL   300000UL  // 5 min between sensor reads
#define RECONNECT_INTERVAL     300000UL  // 5 min between reconnect attempts
#define MAX_CONSECUTIVE_FAILS  10
#define MODEM_COOLDOWN_MS      180000UL  // 3 min after consecutive failures
#define MODEM_RESTART_DELAY_MS 10000UL   // 10 s after power-off before power-on
#define OLED_FIRST_ON_MS       600000UL  // 10 min: keep display on after first send

// Flash storage: magic number "GSM1" to detect valid saved config
#define FLASH_MAGIC 0x47534D31

// ============================================================================
// FLASH STORAGE
// ============================================================================

// STM32H7 requires 32-byte-aligned flash writes
struct __attribute__((aligned(32))) GsmConfig {
  uint32_t magic;
  uint8_t  ratType;      // 0 = NB-IoT, 1 = CAT-M1
  uint8_t  reserved1;
  uint16_t reserved2;
  uint32_t band;
  uint8_t  checksum;
  uint8_t  padding[15];  // pad to exactly 32 bytes
};

GsmConfig g_saved_config;
bool g_has_saved_config = false;

// 128 KB sector in flash bank 2 (avoids code region in bank 1)
FlashIAPBlockDevice flashDevice(0x08100000, 0x20000);

uint8_t calculateChecksum(const GsmConfig& cfg) {
  uint8_t sum = 0;
  sum ^= (cfg.magic >> 24) & 0xFF;
  sum ^= (cfg.magic >> 16) & 0xFF;
  sum ^= (cfg.magic >> 8)  & 0xFF;
  sum ^= cfg.magic & 0xFF;
  sum ^= cfg.ratType;
  sum ^= (cfg.band >> 24) & 0xFF;
  sum ^= (cfg.band >> 16) & 0xFF;
  sum ^= (cfg.band >> 8)  & 0xFF;
  sum ^= cfg.band & 0xFF;
  return sum;
}

bool initFlashStorage() {
  int err = flashDevice.init();
  if (err != 0) {
    Serial.print("Flash: init failed, error ");
    Serial.println(err);
    return false;
  }
  return true;
}

bool loadGsmConfig() {
  if (!initFlashStorage()) {
    g_has_saved_config = false;
    return false;
  }

  int err = flashDevice.read(&g_saved_config, 0, sizeof(GsmConfig));
  flashDevice.deinit();

  if (err != 0) {
    Serial.print("Flash: read failed, error ");
    Serial.println(err);
    g_has_saved_config = false;
    return false;
  }

  if (g_saved_config.magic != FLASH_MAGIC) {
    Serial.println("Flash: no valid config (magic mismatch)");
    g_has_saved_config = false;
    return false;
  }

  if (g_saved_config.checksum != calculateChecksum(g_saved_config)) {
    Serial.println("Flash: config checksum invalid");
    g_has_saved_config = false;
    return false;
  }

  Serial.println("Flash: loaded valid config");
  Serial.print("  RAT: ");
  Serial.println(g_saved_config.ratType == 0 ? "NB-IoT" : "CAT-M1");
  Serial.print("  Band: 0x");
  Serial.println(g_saved_config.band, HEX);

  g_has_saved_config = true;
  return true;
}

void saveGsmConfig(uint8_t ratType, uint32_t band) {
  if (g_has_saved_config &&
      g_saved_config.ratType == ratType &&
      g_saved_config.band == band) {
    Serial.println("Flash: config unchanged, skipping write");
    return;
  }

  GsmConfig config;
  memset(&config, 0, sizeof(GsmConfig));
  config.magic    = FLASH_MAGIC;
  config.ratType  = ratType;
  config.band     = band;
  config.checksum = calculateChecksum(config);

  if (!initFlashStorage()) {
    Serial.println("Flash: cannot save - init failed");
    return;
  }

  size_t eraseSize   = flashDevice.get_erase_size();
  size_t programSize = flashDevice.get_program_size();

  int err = flashDevice.erase(0, eraseSize);
  if (err != 0) {
    Serial.print("Flash: erase failed, error ");
    Serial.println(err);
    flashDevice.deinit();
    return;
  }

  size_t writeSize = sizeof(GsmConfig);
  if (writeSize % programSize != 0) {
    writeSize = ((writeSize / programSize) + 1) * programSize;
  }

  err = flashDevice.program(&config, 0, writeSize);
  flashDevice.deinit();

  if (err != 0) {
    Serial.print("Flash: write failed, error ");
    Serial.println(err);
    return;
  }

  Serial.println("Flash: saved config");
  Serial.print("  RAT: ");
  Serial.println(ratType == 0 ? "NB-IoT" : "CAT-M1");
  Serial.print("  Band: 0x");
  Serial.println(band, HEX);

  g_saved_config     = config;
  g_has_saved_config = true;
}

void clearGsmConfig() {
  if (!initFlashStorage()) return;
  flashDevice.erase(0, flashDevice.get_erase_size());
  flashDevice.deinit();
  g_has_saved_config = false;
  Serial.println("Flash: config cleared");
}

// ============================================================================
// GLOBAL OBJECTS
// ============================================================================

// I2C3 bus for environmental sensors (BME688, LTR390, VEML7700, ENS160, AHT21)
// D11 (PH8) = SDA, D12 (PH7) = SCL
arduino::MbedI2C Wire3(PH_8, PH_7);

Adafruit_SSD1306   display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
Adafruit_BME680    bme(&Wire3);
OneWire            oneWire(DS18B20_PIN);
DallasTemperature  ds18b20(&oneWire);
Adafruit_LTR390    ltr = Adafruit_LTR390();
Adafruit_VEML7700  veml = Adafruit_VEML7700();
SparkFun_ENS160    ens160;
Adafruit_AHTX0     aht21;

Battery battery;
Charger charger;
Board   board;

char pin[]      = SECRET_PIN;
char apn[]      = SECRET_APN;
char username[] = SECRET_USERNAME;
char pass[]     = SECRET_PASSWORD;

GSMClient client;

// Modem HW pins (initial states: enabled, RTS asserted low)
mbed::DigitalOut fst_shdn  (MODEM_FST_SHDN_PIN,   1);
mbed::DigitalOut on_3v3    (MODEM_ON_3V3_PIN,      1);
mbed::DigitalOut emerg_rst (MODEM_EMERG_RST_PIN,   1);
mbed::DigitalOut psm_wakeup(MODEM_PSM_WAKEUP_PIN,  1);
mbed::DigitalOut rts       (MODEM_RTS_PIN,          0);

// GSM.getTime() returns wrong values on this firmware; use NTP exclusively
GSMUDP ntpUDP;
unsigned long g_ntp_epoch  = 0;
unsigned long g_ntp_millis = 0;

// ============================================================================
// GLOBAL STATE
// ============================================================================

// Network info (populated by DebugListener and connection logic)
String g_rat       = "";
long   g_cid       = -1;
int    g_rssi      = 0;
int    g_retry     = -1;
String g_status    = "Init...";
String g_band_info = "";

// OLED / UI
bool          g_oled_power         = false;
bool          g_button_last_state  = HIGH;
unsigned long g_oled_auto_off_at   = 0;
unsigned long g_btn_last_event_ms  = 0;

// PIR motion sensor
bool          g_pir_state            = false;
bool          g_pir_level_prev       = false;
uint8_t       g_pir_count            = 0;
uint8_t       g_pir_count_last_post  = 0;
unsigned long g_pir_last_dispatch_ms = 0;
#define PIR_DEBOUNCE_MS 150

// BME688
float g_temperature  = 0.0;
float g_humidity     = 0.0;
float g_pressure     = 0.0;
bool  g_bme_available = false;

// DS18B20 (soil temperature)
float g_soil_temperature  = 0.0;
bool  g_ds18b20_available = false;

// Soil moisture
int   g_soil_moisture_raw     = 0;
float g_soil_moisture_percent = 0.0;

// LTR390 (UV)
float g_uv_index      = 0.0;
bool  g_ltr_available  = false;

// VEML7700 (ambient light)
float g_veml_lux       = 0.0;
bool  g_veml_available = false;

// ENS160 (air quality)
uint16_t g_eco2 = 0;
uint16_t g_tvoc = 0;
uint8_t  g_aqi  = 0;
bool     g_ens_available = false;

// AHT21 (temperature / humidity)
float g_aht_temp      = 0.0;
float g_aht_humidity   = 0.0;
bool  g_aht_available  = false;

// Rain sensor
bool          g_is_raining     = false;
bool          g_rain_last_hour = false;
unsigned long g_last_rain_time = 0;

// Power management
bool g_power_available = false;

// Timing
unsigned long g_last_api_post  = 0;
bool          g_first_post_done = false;
bool          g_modem_sleeping  = false;

// Network status
bool     g_network_connected  = false;
uint16_t g_post_ok            = 0;
uint16_t g_post_fail          = 0;
uint16_t g_consecutive_fails  = 0;
uint16_t g_full_ok            = 0;
uint16_t g_full_fail          = 0;
uint16_t g_trunc_ok           = 0;
uint16_t g_trunc_fail         = 0;
bool     g_try_truncated      = false;
bool     g_modem_cooling      = false;
unsigned long g_modem_cooldown_start = 0;

// Last successful connection parameters
RadioAccessTechnologyType g_last_rat  = CATNB;
uint32_t                  g_last_band = BAND_3;

// ============================================================================
// LED HELPERS — Portenta H7 LEDs are active LOW
// ============================================================================

void ledInit() {
  pinMode(LEDR, OUTPUT);
  pinMode(LEDG, OUTPUT);
  pinMode(LEDB, OUTPUT);
  ledOff();
  Serial.println("LEDs initialized");
}

void ledOff() {
  digitalWrite(LEDR, HIGH);
  digitalWrite(LEDG, HIGH);
  digitalWrite(LEDB, HIGH);
}

// ledColor and blink functions suppress output when the display is off
void ledRed() {
  if (!g_oled_power) return;
  digitalWrite(LEDR, LOW);
  digitalWrite(LEDG, HIGH);
  digitalWrite(LEDB, HIGH);
}

void ledGreen() {
  if (!g_oled_power) return;
  digitalWrite(LEDR, HIGH);
  digitalWrite(LEDG, LOW);
  digitalWrite(LEDB, HIGH);
}

void ledBlue() {
  if (!g_oled_power) return;
  digitalWrite(LEDR, HIGH);
  digitalWrite(LEDG, HIGH);
  digitalWrite(LEDB, LOW);
}

void blinkBlue(int times, int delayMs = 200) {
  if (!g_oled_power) return;
  for (int i = 0; i < times; i++) {
    ledBlue(); delay(delayMs); ledOff(); delay(delayMs);
  }
}

void blinkGreen(int times, int delayMs = 200) {
  if (!g_oled_power) return;
  for (int i = 0; i < times; i++) {
    ledGreen(); delay(delayMs); ledOff(); delay(delayMs);
  }
}

void blinkRed(int times, int delayMs = 200) {
  if (!g_oled_power) return;
  for (int i = 0; i < times; i++) {
    ledRed(); delay(delayMs); ledOff(); delay(delayMs);
  }
}

// ============================================================================
// OLED HELPERS
// ============================================================================

void oledPowerOn() {
  digitalWrite(OLED_POWER_PIN, HIGH);
  delay(250);
  display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS, false);
  delay(50);
  display.clearDisplay();
  display.display();
  g_oled_power = true;
  updateOLED();
  Serial.println("OLED powered ON");
}

void oledPowerOff() {
  g_oled_power = false;
  digitalWrite(OLED_POWER_PIN, LOW);
  Serial.println("OLED powered OFF");
}

void printLine(uint8_t line, const char* text) {
  if (!g_oled_power || line > 3) return;
  uint8_t y = line * LINE_HEIGHT;
  display.fillRect(0, y, SCREEN_WIDTH, LINE_HEIGHT, SSD1306_BLACK);
  display.setCursor(0, y);
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.print(text);
  display.display();
}

// Line 3: PIR indicator circle + motion count + atmospheric summary
void drawPIRIndicator(bool motionDetected, uint8_t count) {
  if (!g_oled_power) return;
  uint8_t y = 3 * LINE_HEIGHT;
  uint8_t cx = 4, cy = y + 4, r = 3;

  display.fillRect(0, y, SCREEN_WIDTH, LINE_HEIGHT, SSD1306_BLACK);

  if (motionDetected)
    display.fillCircle(cx, cy, r, SSD1306_WHITE);
  else
    display.drawCircle(cx, cy, r, SSD1306_WHITE);

  if (count > 99) count = 99;
  char buf[22];
  snprintf(buf, sizeof(buf), "%02u", count);
  display.setCursor(10, y);
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.print(buf);

  if (g_bme_available) {
    snprintf(buf, sizeof(buf), " %2dC %2d%% %4dhPa",
             (int)g_temperature, (int)g_humidity, (int)g_pressure);
  } else {
    snprintf(buf, sizeof(buf), " --C --%% --hPa");
  }
  display.setCursor(25, y);
  display.print(buf);
  display.display();
}

void updateOLED() {
  char line[22];

  // Line 0: status + POST counters
  if (g_post_fail > 0)
    snprintf(line, sizeof(line), "%s %u(%u)", g_status.c_str(), g_post_ok, g_post_fail);
  else if (g_post_ok > 0)
    snprintf(line, sizeof(line), "%s %u", g_status.c_str(), g_post_ok);
  else
    snprintf(line, sizeof(line), "%s", g_status.c_str());
  printLine(0, line);

  // Line 1: band info + RSSI
  if (g_band_info.length() > 0) {
    if (g_rssi != 0)
      snprintf(line, sizeof(line), "%s %d", g_band_info.c_str(), g_rssi);
    else
      snprintf(line, sizeof(line), "%s", g_band_info.c_str());
  } else {
    snprintf(line, sizeof(line), "Band: --");
  }
  printLine(1, line);

  // Line 2: RAT + CID (connected) or retry count (connecting)
  if (g_rat.length() > 0 && g_cid >= 0)
    snprintf(line, sizeof(line), "RAT:%s CID:%ld", g_rat.c_str(), g_cid);
  else if (g_retry >= 0)
    snprintf(line, sizeof(line), "Retry: %d", g_retry);
  else
    snprintf(line, sizeof(line), "RAT: --");
  printLine(2, line);

  // Line 3: PIR + BME688 summary
  drawPIRIndicator(g_pir_state, g_pir_count);
}

// ============================================================================
// STATE UPDATERS — set a global and refresh the display
// ============================================================================

void updateRSSI(int rssi)          { g_rssi = rssi;   updateOLED(); }
void updateRAT(const String &rat)  { g_rat = rat;     updateOLED(); }
void updateCID(long cid)           { g_cid = cid;     updateOLED(); }
void updateRetry(int retry)        { g_retry = retry;  updateOLED(); }
void updateStatus(const String &s) { g_status = s;     updateOLED(); }

// ============================================================================
// DEBUG LISTENER — parses GSM library debug output to extract network info
// ============================================================================

class DebugListener : public Stream {
public:
  DebugListener(Stream* forwardTo) : target(forwardTo) {}

  size_t write(uint8_t c) override {
    if (target) target->write(c);
    if (c == '\n') { processLine(buffer); buffer = ""; }
    else if (c != '\r') buffer += (char)c;
    return 1;
  }

  int  available() override { return 0; }
  int  read()      override { return -1; }
  int  peek()      override { return -1; }
  void flush()     override {}

private:
  Stream* target;
  String buffer;

  void processLine(const String &line) {
    int pos;

    pos = line.indexOf("RSSI:");
    if (pos >= 0) {
      String v = line.substring(pos + 5);
      v.trim();
      updateRSSI(v.toInt());
    }

    pos = line.indexOf("RAT changed:");
    if (pos >= 0) {
      int colon = line.indexOf(':', pos);
      if (colon >= 0) {
        String rat = line.substring(colon + 1);
        rat.trim();
        updateRAT(rat);
      }
    }

    pos = line.indexOf("Cellular ID changed:");
    if (pos >= 0) {
      int colon = line.indexOf(':', pos);
      if (colon >= 0) {
        String cidStr = line.substring(colon + 1);
        cidStr.trim();
        updateCID(cidStr.toInt());
      }
    }

    pos = line.indexOf("retry count");
    if (pos >= 0) {
      int sp = line.lastIndexOf(' ');
      if (sp >= 0 && sp + 1 < (int)line.length()) {
        String rs = line.substring(sp + 1);
        rs.trim();
        int rv = rs.toInt();
        if (rv >= 0) updateRetry(rv);
      }
    }

    if (line.indexOf(" Searching Network") >= 0)   updateStatus("Searching...");
    if (line.indexOf(" Registration Denied") >= 0) updateStatus("Reg Denied");
  }
};

DebugListener debugListener(&Serial);

// ============================================================================
// INPUT POLLING — button and PIR sensor
// ============================================================================

void onButtonPressed() {
  if (g_oled_power) oledPowerOff(); else oledPowerOn();
}

// Polls button for falling edge (HIGH -> LOW) with 1 s debounce
void pollButton() {
  bool state = digitalRead(BUTTON_PIN);
  if (state == LOW && g_button_last_state == HIGH) {
    if (millis() - g_btn_last_event_ms >= 1000) {
      g_btn_last_event_ms = millis();
      onButtonPressed();
    }
  }
  g_button_last_state = state;
}

void handlePIRChange() {
  Serial.print("PIR ");
  Serial.print(g_pir_state ? "motion" : "idle");
  Serial.print("  count: ");
  Serial.println(g_pir_count);
  drawPIRIndicator(g_pir_state, g_pir_count);
}

// Polls PIR pin for edge transitions, counts rising edges, throttles display updates
void pollPIRSensor() {
  bool level = (digitalRead(PIR_PIN) == HIGH);
  if (level && !g_pir_level_prev) {
    g_pir_count++;
  }
  if (level != g_pir_level_prev) {
    g_pir_state      = level;
    g_pir_level_prev = level;
    unsigned long now = millis();
    if (now - g_pir_last_dispatch_ms >= PIR_DEBOUNCE_MS) {
      g_pir_last_dispatch_ms = now;
      handlePIRChange();
    }
  }
}

// ============================================================================
// SENSOR READING
// ============================================================================

void readBME688() {
  if (!g_bme_available) return;
  if (bme.performReading()) {
    g_temperature = bme.temperature;
    g_humidity    = bme.humidity;
    g_pressure    = bme.pressure / 100.0;
    Serial.print("BME688: ");
    Serial.print(g_temperature);
    Serial.print(" C, ");
    Serial.print(g_humidity);
    Serial.print(" %, ");
    Serial.print(g_pressure);
    Serial.println(" hPa");
    drawPIRIndicator(g_pir_state, g_pir_count);
  } else {
    Serial.println("BME688 reading failed");
  }
}

void readSoilTemperature() {
  if (!g_ds18b20_available) return;
  float temp = DEVICE_DISCONNECTED_C;
  for (int attempt = 0; attempt < 5; attempt++) {
    ds18b20.requestTemperatures();
    temp = ds18b20.getTempCByIndex(0);
    if (temp != DEVICE_DISCONNECTED_C) break;
    delay(10);
  }
  if (temp == DEVICE_DISCONNECTED_C) {
    Serial.println("DS18B20 read error");
    return;
  }
  g_soil_temperature = temp;
  Serial.print("Soil temp: ");
  Serial.print(g_soil_temperature, 1);
  Serial.println(" C");
}

void readSoilMoisture() {
  g_soil_moisture_raw = analogRead(SOIL_MOISTURE_PIN);
  // DRY (high ADC) = 0 %, WET (low ADC) = 100 %
  float pct = (float)(SOIL_MOISTURE_DRY - g_soil_moisture_raw)
            / (float)(SOIL_MOISTURE_DRY - SOIL_MOISTURE_WET) * 100.0;
  g_soil_moisture_percent = constrain(pct, 0.0f, 100.0f);
  Serial.print("Soil moisture raw: ");
  Serial.print(g_soil_moisture_raw);
  Serial.print(", ");
  Serial.print(g_soil_moisture_percent, 1);
  Serial.println("%");
}

void readLTR390() {
  if (!g_ltr_available) return;
  if (ltr.newDataAvailable()) {
    // Approximate UV index from raw UVS count (gain=3x, integration=100 ms)
    g_uv_index = ltr.readUVS() / 2300.0;
    Serial.print("UV index: ");
    Serial.println(g_uv_index, 2);
  }
}

void readVEML7700() {
  if (!g_veml_available) return;
  g_veml_lux = veml.readLux();
  Serial.print("Lux: ");
  Serial.println(g_veml_lux, 1);
}

void readENS160() {
  if (!g_ens_available) return;
  if (ens160.checkDataStatus()) {
    g_aqi  = ens160.getAQI();
    g_tvoc = ens160.getTVOC();
    g_eco2 = ens160.getECO2();
    Serial.print("AQI: ");
    Serial.print(g_aqi);
    Serial.print("  TVOC: ");
    Serial.print(g_tvoc);
    Serial.print(" ppb  eCO2: ");
    Serial.print(g_eco2);
    Serial.println(" ppm");
  }
}

void readAHT21() {
  if (!g_aht_available) return;
  sensors_event_t hum, tmp;
  aht21.getEvent(&hum, &tmp);
  g_aht_temp     = tmp.temperature;
  g_aht_humidity = hum.relative_humidity;
  Serial.print("AHT21: ");
  Serial.print(g_aht_temp, 1);
  Serial.print(" C, ");
  Serial.print(g_aht_humidity, 1);
  Serial.println("%");
}

void readRainSensor() {
  g_is_raining = (digitalRead(RAIN_SENSOR_PIN) == LOW);
  if (g_is_raining) g_last_rain_time = millis();
  g_rain_last_hour = (g_last_rain_time > 0 &&
                      (millis() - g_last_rain_time) < 3600000UL);
}

// ============================================================================
// SENSOR POWER — sleep / wake to reduce current between reads
// ============================================================================

// BME688 auto-sleeps in forced mode (0.15 uA).
// AHT21 has no low-power command.
// ENS160 uses IDLE (not DEEP_SLEEP) to avoid the 3-minute warm-up penalty.

void sensorsSleep() {
  if (g_ltr_available)  ltr.enable(false);
  if (g_veml_available) veml.enable(false);
  if (g_ens_available)  ens160.setOperatingMode(SFE_ENS160_IDLE);
  Serial.println("Sensors sleeping");
}

void sensorsWake() {
  if (g_ltr_available) {
    ltr.enable(true);
    ltr.setMode(LTR390_MODE_UVS);  // enable() touches MAIN_CTRL — restore mode
  }
  if (g_veml_available) veml.enable(true);
  if (g_ens_available)  ens160.setOperatingMode(SFE_ENS160_STANDARD);
  Serial.println("Sensors awake");
}

// ============================================================================
// POWER STATS
// ============================================================================

void printPowerStats() {
  if (!g_power_available) return;
  Serial.print("Power: ");
  Serial.print(battery.voltage() * 1000);
  Serial.print(" mV  SoC: ");
  Serial.print(battery.percentage());
  Serial.print("%  I: ");
  Serial.print(battery.current());
  Serial.println(" mA");
}

// ============================================================================
// TIME — NTP sync (GSM.getTime() is unreliable on this firmware)
// ============================================================================

bool syncNTPTime() {
  updateStatus("Time sync...");
  const char* servers[] = {
    "time.cloudflare.com", "time.google.com", "ntp1.inrim.it"
  };
  for (int i = 0; i < 3; i++) {
    Serial.print("NTP: ");
    Serial.println(servers[i]);
    NTPClient ntp(ntpUDP, servers[i], 0);
    ntp.begin();
    bool ok = ntp.forceUpdate();
    ntp.end();
    if (ok) {
      g_ntp_epoch  = ntp.getEpochTime();
      g_ntp_millis = millis();
      Serial.print("NTP OK: ");
      Serial.println(g_ntp_epoch);
      return true;
    }
    Serial.print("  ");
    Serial.print(servers[i]);
    Serial.println(" failed");
  }
  Serial.println("NTP: all servers failed");
  return false;
}

String getISO8601Timestamp() {
  if (g_ntp_epoch == 0) return "1970-01-01T00:00:00Z";
  unsigned long epoch = g_ntp_epoch + (millis() - g_ntp_millis) / 1000;
  time_t rawtime = epoch;
  struct tm* ti  = gmtime(&rawtime);
  char buf[25];
  snprintf(buf, sizeof(buf), "%04d-%02d-%02dT%02d:%02d:%02dZ",
           ti->tm_year + 1900, ti->tm_mon + 1, ti->tm_mday,
           ti->tm_hour, ti->tm_min, ti->tm_sec);
  return String(buf);
}

// ============================================================================
// JSON PAYLOADS
// ============================================================================

String buildJsonPayload() {
  uint8_t motion_count = g_pir_count - g_pir_count_last_post;
  if (g_pir_count < g_pir_count_last_post) motion_count = g_pir_count;

  String j;
  j.reserve(600);

  j = "{";
  j += "\"station_id\":\"" + String(STATION_ID) + "\",";
  j += "\"timestamp\":\"" + getISO8601Timestamp() + "\",";
  j += "\"location\":{";
  j += "\"latitude\":" + String(LATITUDE, 4) + ",";
  j += "\"longitude\":" + String(LONGITUDE, 4) + ",";
  j += "\"altitude\":" + String(ALTITUDE) + ",";
  j += "\"trail_name\":\"" + String(TRAIL_NAME) + "\"";
  j += "},";

  j += "\"power\":{";
  if (g_power_available) {
    ChargingState cs = charger.getState();
    bool charging = (cs == ChargingState::preCharge ||
                     cs == ChargingState::fastChargeConstantCurrent ||
                     cs == ChargingState::fastChargeConstantVoltage ||
                     cs == ChargingState::endOfCharge);
    j += "\"percentage\":" + String(battery.percentage()) + ",";
    j += "\"voltage_mv\":" + String((int)(battery.voltage() * 1000)) + ",";
    j += "\"is_charging\":" + String(charging ? "true" : "false");
  } else {
    j += "\"percentage\":null,\"voltage_mv\":null,\"is_charging\":null";
  }
  j += "},";

  j += "\"sensors\":{";

  j += "\"atmospheric\":{";
  if (g_bme_available) {
    j += "\"temperature\":" + String(g_temperature, 1) + ",";
    j += "\"humidity\":" + String(g_humidity, 1) + ",";
    j += "\"pressure\":" + String(g_pressure, 1);
  } else {
    j += "\"temperature\":null,\"humidity\":null,\"pressure\":null";
  }
  j += "},";

  j += "\"light\":{";
  j += "\"uv_index\":" + (g_ltr_available  ? String(g_uv_index, 2) : String("null")) + ",";
  j += "\"lux\":"      + (g_veml_available ? String(g_veml_lux, 1) : String("null"));
  j += "},";

  j += "\"soil\":{";
  j += "\"temperature\":" + (g_ds18b20_available ? String(g_soil_temperature, 1) : String("null")) + ",";
  j += "\"moisture_percent\":" + String(g_soil_moisture_percent, 1);
  j += "},";

  j += "\"air_quality\":{";
  if (g_ens_available) {
    j += "\"co2_ppm\":" + String(g_eco2) + ",";
    j += "\"tvoc_ppb\":" + String(g_tvoc) + ",";
    j += "\"aqi\":" + String(g_aqi);
  } else {
    j += "\"co2_ppm\":null,\"tvoc_ppb\":null,\"aqi\":null";
  }
  j += "},";

  j += "\"precipitation\":{";
  j += "\"is_raining\":" + String(g_is_raining ? "true" : "false") + ",";
  j += "\"rain_detected_last_hour\":" + String(g_rain_last_hour ? "true" : "false");
  j += "},";

  j += "\"trail_activity\":{";
  j += "\"motion_count\":" + String(motion_count) + ",";
  j += "\"period_minutes\":" + String(POST_INTERVAL / 60000);
  j += "}";

  j += "}}";
  return j;
}

// Minimal payload for diagnosing connectivity / payload-size issues
String buildTruncatedPayload() {
  String j = "{";
  j += "\"station_id\":\"" + String(STATION_ID) + "\",";
  j += "\"timestamp\":\"" + getISO8601Timestamp() + "\",";
  j += "\"sensors\":{\"atmospheric\":{";
  j += "\"temperature\":" + (g_bme_available ? String(g_temperature, 1) : String("null"));
  j += "}}}";
  return j;
}

// ============================================================================
// MODEM CONTROL
// ============================================================================

void modemHWPowerOn() {
  fst_shdn   = 1;
  on_3v3     = 1;
  emerg_rst  = 1;
  psm_wakeup = 1;
  rts        = 0;
}

void modemHWPowerOff() {
  fst_shdn = 0;
  on_3v3   = 0;
}

void modemHWReset() {
  emerg_rst = 0;
  delay(200);
  emerg_rst = 1;
}

void modemPowerOn() {
  modemHWPowerOn();
  Serial.println("Modem HW powered on");
}

void modemPowerOff() {
  GSM.end();
  GSM.off();
  modemHWPowerOff();
  g_network_connected = false;
  Serial.println("Modem power OFF");
}

// ============================================================================
// NETWORK — HTTP POST, API send, GSM connection, post stats
// ============================================================================

bool modemHttpPost(const String& jsonPayload) {
  Serial.print("Payload size: ");
  Serial.println(jsonPayload.length());

  if (!client.connect(API_SERVER, API_PORT)) {
    Serial.println("Connection to server failed");
    return false;
  }

  if (!client.connected()) {
    Serial.println("Client disconnected before write");
    client.stop();
    return false;
  }

  client.print("POST ");
  client.print(API_PATH);
  client.println(" HTTP/1.1");
  client.print("Host: ");
  client.println(API_SERVER);
  client.println("Content-Type: application/json");
  client.print("Content-Length: ");
  client.println(jsonPayload.length());
  client.println("Connection: close");
  client.println();
  client.print(jsonPayload);

  unsigned long t = millis();
  while (!client.available() && millis() - t < 15000) {
    delay(100);
    yield();
  }

  String resp;
  unsigned long deadline = millis() + 10000UL;
  while (millis() < deadline) {
    while (client.available()) {
      resp += (char)client.read();
      deadline = millis() + 3000UL;
    }
    if (!client.connected()) break;
    delay(50);
  }
  client.stop();

  Serial.println("--- HTTP RESPONSE ---");
  Serial.println(resp);
  Serial.println("--- END RESPONSE ---");

  return resp.indexOf("HTTP/1.1 20") >= 0 || resp.indexOf("HTTP/1.0 20") >= 0;
}

void printPostStats() {
  Serial.println("--- POST STATS ---");
  Serial.print("Total: ");
  Serial.print(g_post_ok + g_post_fail);
  Serial.print("  OK: ");
  Serial.print(g_post_ok);
  Serial.print("  FAIL: ");
  Serial.println(g_post_fail);
  Serial.print("Full   OK: ");
  Serial.print(g_full_ok);
  Serial.print("  FAIL: ");
  Serial.println(g_full_fail);
  Serial.print("Trunc  OK: ");
  Serial.print(g_trunc_ok);
  Serial.print("  FAIL: ");
  Serial.println(g_trunc_fail);
  Serial.println("------------------");
}

void sendDataToAPI() {
  if (!g_network_connected || g_modem_cooling) {
    Serial.println("No network or modem cooling - skipping post");
    return;
  }

  IPAddress ip = GSM.localIP();
  if (ip == IPAddress(0, 0, 0, 0)) {
    Serial.println("IP lost (0.0.0.0) - marking network down");
    g_network_connected = false;
    updateStatus("No IP!");
    return;
  }

  bool truncated = g_try_truncated;
  String json = truncated ? buildTruncatedPayload() : buildJsonPayload();
  Serial.print("JSON (");
  Serial.print(truncated ? "truncated" : "full");
  Serial.print(", ");
  Serial.print(json.length());
  Serial.println(" bytes):");
  Serial.println(json);

  bool ok = modemHttpPost(json);
  Serial.print("POST result: ");
  Serial.println(ok ? "OK" : "FAIL");

  if (ok) {
    g_post_ok++;
    g_consecutive_fails = 0;
    if (truncated) g_trunc_ok++; else g_full_ok++;
    blinkGreen(2);
    g_pir_count_last_post = g_pir_count;
    g_try_truncated = false;
  } else {
    g_post_fail++;
    g_consecutive_fails++;
    if (truncated) g_trunc_fail++; else g_full_fail++;
    g_try_truncated = !truncated;
    blinkRed(2);
    Serial.print("Consecutive fails: ");
    Serial.println(g_consecutive_fails);

    if (g_consecutive_fails >= MAX_CONSECUTIVE_FAILS) {
      Serial.println("Too many failures - entering modem cooldown");
      modemPowerOff();
      g_modem_cooling = true;
      g_modem_cooldown_start = millis();
      updateStatus("Cooling");
    }
  }

  printPostStats();
  updateOLED();
}

// Unified GSM connection: tries saved flash config first, then cycles through
// all RAT + band combinations.  Saves successful config to flash.
//
// isInitialConnect = true  — modem already settled in setup(); waits for IP up
//                            to 120 s (NB-IoT PDP activation can be slow).
// isInitialConnect = false — resets modem state before each attempt.
bool connectGSM(bool isInitialConnect) {
  const uint32_t ALL_BANDS = BAND_1 | BAND_3 | BAND_8 | BAND_20 | BAND_28;
  const RadioAccessTechnologyType ratTypes[] = {
    CATNB, CATNB, CATNB, CATNB, CATNB, CATNB,
    CATM1, CATM1, CATM1, CATM1, CATM1, CATM1
  };
  const uint32_t bands[] = {
    ALL_BANDS, BAND_1, BAND_3, BAND_8, BAND_20, BAND_28,
    ALL_BANDS, BAND_1, BAND_3, BAND_8, BAND_20, BAND_28
  };
  const char* ratNames[]  = { "NB","NB","NB","NB","NB","NB",
                               "M1","M1","M1","M1","M1","M1" };
  const char* bandNames[] = { "ALL","B1","B3","B8","B20","B28",
                               "ALL","B1","B3","B8","B20","B28" };
  const int NUM_ATTEMPTS = 12;
  const int SETTLE_MS    = 20000;

  bool     registered  = false;
  uint8_t  successRat  = 0;
  uint32_t successBand = 0;

  // On reconnect the modem was just powered on; reset library state first.
  // On initial connect the modem already settled in setup().
  bool modemNeedsSettle = !isInitialConnect;

  // --- Try saved flash config first ---
  if (g_has_saved_config) {
    Serial.println("Trying saved flash config...");
    RadioAccessTechnologyType savedRat =
        (g_saved_config.ratType == 0) ? CATNB : CATM1;
    const char* savedRatName =
        (g_saved_config.ratType == 0) ? "NB" : "M1";

    updateStatus("Saved cfg");
    g_band_info = String(savedRatName) + " SAVED";
    updateOLED();

    if (modemNeedsSettle) {
      GSM.end();
      GSM.off();
      countdownWait(SETTLE_MS, "Reset");
    }

    blinkBlue(2);
    ledBlue();
    registered = GSM.begin(pin, apn, username, pass,
                           savedRat, g_saved_config.band);

    if (registered) {
      ledGreen();
      Serial.println("Connected with saved flash config");
      g_last_rat  = savedRat;
      g_last_band = g_saved_config.band;
      successRat  = g_saved_config.ratType;
      successBand = g_saved_config.band;
      g_band_info = String(savedRatName) + " SAVED";
    } else {
      blinkRed(3);
      Serial.println("Saved config failed, trying other combinations...");
      GSM.end();
      GSM.off();
    }
    modemNeedsSettle = !registered;
  }

  // --- Cycle through all RAT + band combinations ---
  for (int i = 0; i < NUM_ATTEMPTS && !registered; i++) {
    char statusMsg[20];
    snprintf(statusMsg, sizeof(statusMsg), "%s %s %d/%d",
             ratNames[i], bandNames[i], i + 1, NUM_ATTEMPTS);
    updateStatus(statusMsg);
    g_band_info = String(ratNames[i]) + " " + String(bandNames[i]);
    updateOLED();

    if (modemNeedsSettle) {
      countdownWait(SETTLE_MS, "Settle");
    }
    modemNeedsSettle = false;

    blinkBlue(2);
    ledBlue();
    registered = GSM.begin(pin, apn, username, pass,
                           ratTypes[i], bands[i]);

    if (registered) {
      ledGreen();
      Serial.print("Connected with ");
      Serial.print(ratNames[i]);
      Serial.print(" ");
      Serial.println(bandNames[i]);
      g_last_rat  = ratTypes[i];
      g_last_band = bands[i];
      g_band_info = String(ratNames[i]) + " " + String(bandNames[i]);
      successRat  = (ratTypes[i] == CATNB) ? 0 : 1;
      successBand = bands[i];
    } else {
      blinkRed(3);
      if (i < NUM_ATTEMPTS - 1) {
        GSM.end();
        GSM.off();
        modemNeedsSettle = true;
      }
    }
  }

  if (!registered) {
    blinkRed(5);
    ledRed();
    Serial.println("GSM registration failed after all attempts");
    g_network_connected = false;
    updateStatus(isInitialConnect ? "Reg Failed" : "No Network");
    return false;
  }

  saveGsmConfig(successRat, successBand);
  g_network_connected = true;
  updateStatus("Registered");

  // On initial connect, wait for PDP context / IP (can take 60-90 s on NB-IoT)
  if (isInitialConnect) {
    Serial.println("Waiting for IP address (up to 120 s)...");
    updateStatus("Waiting IP...");
    IPAddress ip;
    unsigned long ipStart = millis();
    while (millis() - ipStart < 120000UL) {
      ip = GSM.localIP();
      if (ip != IPAddress(0, 0, 0, 0)) break;
      Serial.print(".");
      delay(3000);
    }
    Serial.println();

    if (ip == IPAddress(0, 0, 0, 0)) {
      Serial.println("No IP, trying ping to kickstart data path...");
      GSM.ping("8.8.8.8");
      delay(5000);
      ip = GSM.localIP();
    }

    if (ip == IPAddress(0, 0, 0, 0)) {
      Serial.println("WARNING: No IP obtained");
      updateStatus("No IP!");
      g_network_connected = false;
      return false;
    }
  }

  Serial.print("Local IP: ");
  Serial.println(GSM.localIP());
  Serial.print("Ping 8.8.8.8: ");
  Serial.print(GSM.ping("8.8.8.8"));
  Serial.println(" ms");
  delay(1000);
  updateStatus("IP OK");

  if (syncNTPTime()) {
    time_t rawtime = g_ntp_epoch;
    struct tm* ti  = gmtime(&rawtime);
    char ts[20];
    snprintf(ts, sizeof(ts), "%02d:%02d:%02d",
             ti->tm_hour, ti->tm_min, ti->tm_sec);
    Serial.print("Time: ");
    Serial.println(ts);
    updateStatus("Time OK");
  } else {
    Serial.println("NTP failed - timestamps will show 1970-01-01");
    updateStatus("No Time");
  }

  return true;
}

// ============================================================================
// UTILITIES
// ============================================================================

// Blocking countdown that keeps polling button + PIR sensor
void countdownWait(int totalMs, const char* label) {
  for (int s = totalMs / 1000; s > 0; s--) {
    char buf[20];
    snprintf(buf, sizeof(buf), "%s %ds", label, s);
    updateStatus(buf);
    Serial.print(s);
    Serial.print("s \r");
    unsigned long t = millis();
    while (millis() - t < 1000) {
      pollButton();
      pollPIRSensor();
      delay(20);
    }
  }
  Serial.println();
}

// ============================================================================
// setup()
// ============================================================================

void setup() {
  modemPowerOn();
  Serial.begin(9600);
  Serial.println("Starting... v0.2");

  // Power management (Battery / Charger / Board)
  if (board.begin() && battery.begin() && charger.begin()) {
    g_power_available = true;
    Serial.println("Power management initialized");
  } else {
    g_power_available = false;
    Serial.println("Power management not available");
  }

  ledInit();

  // OLED power MOSFET (start off)
  pinMode(OLED_POWER_PIN, OUTPUT);
  digitalWrite(OLED_POWER_PIN, LOW);

  // Button (active LOW, internal pullup)
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  // PIR sensor
  pinMode(PIR_PIN, INPUT_PULLDOWN);

  // I2C buses
  Wire.begin();
  Wire3.begin();

  // DS18B20 soil temperature
  ds18b20.begin();
  g_ds18b20_available = (ds18b20.getDeviceCount() > 0);
  if (g_ds18b20_available) {
    Serial.print("DS18B20 found, devices: ");
    Serial.println(ds18b20.getDeviceCount());
  } else {
    Serial.println("DS18B20 not found");
  }

  // Soil moisture + rain sensor
  pinMode(SOIL_MOISTURE_PIN, INPUT);
  pinMode(RAIN_SENSOR_PIN, INPUT_PULLUP);

  // BME688 on Wire3
  g_bme_available = bme.begin(BME688_I2C_ADDR);
  if (g_bme_available) {
    bme.setTemperatureOversampling(BME680_OS_8X);
    bme.setHumidityOversampling(BME680_OS_2X);
    bme.setPressureOversampling(BME680_OS_4X);
    bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
    bme.setGasHeater(320, 150);
    Serial.println("BME688 found on Wire3");
  } else {
    Serial.println("BME688 not found");
  }

  // LTR390 UV sensor on Wire3
  g_ltr_available = ltr.begin(&Wire3);
  if (g_ltr_available) {
    ltr.setMode(LTR390_MODE_UVS);
    ltr.setGain(LTR390_GAIN_3);
    ltr.setResolution(LTR390_RESOLUTION_16BIT);
    Serial.println("LTR390 found on Wire3");
  } else {
    Serial.println("LTR390 not found");
  }

  // VEML7700 ambient light on Wire3
  g_veml_available = veml.begin(&Wire3);
  if (g_veml_available) {
    veml.setGain(VEML7700_GAIN_1);
    veml.setIntegrationTime(VEML7700_IT_100MS);
    Serial.println("VEML7700 found on Wire3");
  } else {
    Serial.println("VEML7700 not found");
  }

  // ENS160 air quality on Wire3
  g_ens_available = ens160.begin(Wire3, 0x52);
  if (g_ens_available) {
    ens160.setOperatingMode(SFE_ENS160_STANDARD);
    Serial.println("ENS160 found on Wire3");
  } else {
    Serial.println("ENS160 not found");
  }

  // AHT21 temperature/humidity on Wire3
  g_aht_available = aht21.begin(&Wire3);
  if (g_aht_available) {
    Serial.println("AHT21 found on Wire3");
  } else {
    Serial.println("AHT21 not found");
  }

  oledPowerOn();
  updateStatus("Init...");

  Debug.setDebugOutputStream(&debugListener);
  Debug.setDebugLevel(DBG_VERBOSE);

  Serial.println("Starting GSM registration");
  loadGsmConfig();

  // Let the radio finish its initial cell scan before the first GSM.begin()
  const int MODEM_SETTLE_MS = 30000;
  countdownWait(MODEM_SETTLE_MS, "Settle");

  bool connected = connectGSM(true);

  if (!connected) {
    Serial.println("Will continue with sensors only - no network");
    modemPowerOff();
  }

  // First sensor read + API post
  if (g_network_connected) {
    sensorsWake();
    readBME688();
    readSoilTemperature();
    readSoilMoisture();
    readLTR390();
    readVEML7700();
    readENS160();
    readAHT21();
    readRainSensor();
    printPowerStats();
    sendDataToAPI();
    g_first_post_done  = true;
    g_last_api_post    = millis();
    g_oled_auto_off_at = millis() + OLED_FIRST_ON_MS;
    if (!g_modem_cooling) {
      modemPowerOff();
      g_modem_sleeping = true;
    }
  } else {
    modemPowerOff();
  }
  sensorsSleep();
}

// ============================================================================
// loop()
// ============================================================================

void loop() {
  static unsigned long lastSensorRead      = 0;
  static unsigned long lastReconnectAttempt = 0;

  pollPIRSensor();
  pollButton();

  unsigned long now = millis();

  // Auto-off OLED after scheduled timeout
  if (g_oled_auto_off_at > 0 && now >= g_oled_auto_off_at && g_oled_power) {
    oledPowerOff();
    g_oled_auto_off_at = 0;
  }

  // Read all sensors periodically
  if (now - lastSensorRead >= SENSOR_READ_INTERVAL) {
    lastSensorRead = now;
    sensorsWake();
    readBME688();
    readSoilTemperature();
    readSoilMoisture();
    readLTR390();
    readVEML7700();
    readENS160();
    readAHT21();
    readRainSensor();
    printPowerStats();
    sensorsSleep();
  }

  // Re-sync NTP every 24 hours
  if (g_network_connected && g_ntp_epoch > 0 &&
      (now - g_ntp_millis >= 86400000UL)) {
    syncNTPTime();
  }

  // Post sensor data to API
  if (g_first_post_done && (millis() - g_last_api_post >= POST_INTERVAL)) {
    if (g_modem_sleeping && !g_modem_cooling) {
      modemPowerOn();
      delay(MODEM_RESTART_DELAY_MS);
      connectGSM(false);
      g_modem_sleeping = false;
    }
    sendDataToAPI();
    g_last_api_post    = millis();
    g_oled_auto_off_at = millis() + 20000UL;
    if (!g_modem_cooling) {
      modemPowerOff();
      g_modem_sleeping = true;
    }
  }

  // Handle modem cooldown expiry
  if (g_modem_cooling && (now - g_modem_cooldown_start >= MODEM_COOLDOWN_MS)) {
    Serial.println("Cooldown expired - restarting modem");
    g_modem_cooling     = false;
    g_modem_sleeping    = false;
    g_consecutive_fails = 0;
    modemPowerOn();
    delay(MODEM_RESTART_DELAY_MS);
    connectGSM(false);
    lastReconnectAttempt = millis();
  }

  // Reconnect if network is down (not during cooldown or intentional sleep)
  if (!g_modem_cooling && !g_modem_sleeping && !g_network_connected &&
      (now - lastReconnectAttempt >= RECONNECT_INTERVAL)) {
    lastReconnectAttempt = now;
    connectGSM(false);
  }

  delay(50);
}
