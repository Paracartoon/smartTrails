# PIR Motion Sensor with Cellular Data Transmission

Arduino-based motion detection system using PIR sensor and NB-IoT cellular connectivity for remote environmental monitoring.

## Hardware

- **Arduino Portenta H7**
- **Arduino Portenta Cat.M1/NB-IoT GNSS Shield**
- **PIR Motion Sensor** (HC-SR501 or similar)
- **Cellular antenna**
- **NB-IoT SIM card**

## Features

- Motion detection using PIR sensor
- 30-second PIR stabilization period on startup
- Cellular connectivity via NB-IoT (Cat-M1/NB-IoT)
- HTTP POST requests to REST API
- JSON payload with motion events and timestamps
- Automatic DNS resolution
- Network stability checks before transmission

## Hardware Connections

```
PIR Sensor → Arduino Portenta H7
- VCC → 5V
- GND → GND  
- OUT → A0

Cellular Shield
- Mounted on Portenta H7 high-density connectors
- Antenna connected to shield's antenna port
- SIM card inserted in shield's SIM slot
```

## Setup

1. **Install Arduino IDE** and required libraries:
   - Arduino Mbed OS Portenta Boards
   - GSM library (included in Mbed core)

2. **Configure SIM credentials:**
   - Copy `arduino_secrets.h` 
   - Fill in your SIM PIN, APN, username, and password

3. **Upload code:**
   - Connect Portenta H7 via USB
   - Select board: Tools → Board → Arduino Portenta H7 (M7 core)
   - Upload the sketch

4. **Monitor serial output:**
   - Open Serial Monitor at 9600 baud
   - Watch for network connection and motion detection events

## API Endpoint

Current configuration sends data to: `http://api.restful-api.dev/objects`

Modify `server` and `port` constants to use your own API endpoint.

### JSON Payload Format

```json
{
  "name": "PIR Motion Sensor",
  "data": {
    "motion": true,
    "timestamp": "246300"
  }
}
```

## Troubleshooting

See [TECHNICAL_REPORT.md](TECHNICAL_REPORT.md) for detailed debugging information and lessons learned.

## Power Considerations

⚠️ **Important:** PIR sensor requires 5V power from Portenta's 5V pin. Do not use 3.3V - it will cause false readings.

## Future Enhancements

- Deep sleep mode for battery operation
- Temperature sensor integration
- GPS coordinates in payload
- Local logging to SD card
- Battery voltage monitoring
