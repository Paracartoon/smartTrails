# SmartTrails

End-to-end trail monitoring system with Arduino sensors, Django backend, and native iOS/watchOS apps.

## Architecture

```
┌─────────────┐      HTTP POST       ┌─────────────┐      HTTP GET       ┌─────────────┐
│   Arduino   │  ─────────────────►  │   Django    │  ◄───────────────   │  iOS App    │
│   Sensors   │    sensor data       │   Backend   │    station data     │  watchOS    │
└─────────────┘                      └─────────────┘                     └─────────────┘
                                           │
                                           ▼
                                     ┌───────────┐
                                     │PostgreSQL │
                                     │    DB     │
                                     └───────────┘
```

## Components

### Arduino (`/Arduino`)

Arduino-based sensor station using Portenta H7 with NB-IoT cellular connectivity.

**Hardware:**
- Arduino Portenta H7
- Arduino Portenta Cat.M1/NB-IoT GNSS Shield
- PIR Motion Sensor (HC-SR501)
- Cellular antenna + NB-IoT SIM

**Sensors collected:**
- Temperature, humidity, pressure (atmospheric)
- UV index, light intensity (lux)
- Soil moisture
- CO2 levels (air quality)
- Rain detection
- Trail activity (PIR motion count)

### Django Backend (`/django`)

REST API for receiving sensor data from Arduino and serving it to mobile apps.

**Apps:**
- `stations` - Station metadata (location, altitude, trail name)
- `sensors` - Sensor reading models (6 separate tables)
- `api` - REST endpoints

**Endpoints:**
- `POST /api/v1/sensors/data/` - Receive sensor data from Arduino
- `GET /api/v1/stations/<station_id>/data/` - Get latest readings for mobile apps
- `GET /api/v1/health/` - Health check

### iOS App (`/iOS/SmartTrails`)

Native SwiftUI app displaying real-time trail conditions.

**Features:**
- Dashboard with all sensor readings
- Color-coded sections (atmospheric, light, soil, air quality, precipitation, trail activity)
- Pull-to-refresh
- Auto-refresh every 5 minutes***
- Danger indicators for hazardous conditions

**Requirements:**
- iOS 17+
- Xcode 15+

### watchOS App (`/iOS/SmartTrails Watch App`)

Companion Apple Watch app with the same sensor data.

**Features:**
- Compact dashboard optimized for watch
- Digital Crown refresh
- Black background for OLED
- Relative timestamp display

**Requirements:**
- watchOS 10+


## API Response Format

```json
{
  "station_id": "mombarone-san-carlo",
  "timestamp": "2024-11-30T17:30:00Z",
  "location": {
    "latitude": 45.5615,
    "longitude": 8.0573,
    "altitude": 1250,
    "trail_name": "Sentiero Graglia"
  },
  "sensors": {
    "atmospheric": {
      "temperature": 12.5,
      "temperature_is_dangerous": false,
      "humidity": 65.0,
      "humidity_is_dangerous": false,
      "pressure": 875.3,
      "pressure_is_dangerous": false
    },
    "light": {
      "uv_index": 3.2,
      "uv_index_is_dangerous": false,
      "lux": 45000,
      "lux_is_dangerous": false
    },
    "soil": {
      "moisture_percent": 45.5,
      "moisture_percent_is_dangerous": false
    },
    "air_quality": {
      "co2_ppm": 420,
      "co2_ppm_is_dangerous": false
    },
    "precipitation": {
      "is_raining": false,
      "is_raining_is_dangerous": false,
      "rain_detected_last_hour": true,
      "rain_detected_last_hour_is_dangerous": false
    },
    "trail_activity": {
      "motion_count": 12,
      "motion_count_is_dangerous": false,
      "period_minutes": 60
    }
  }
}
```

## Project Structure

```
smartTrails/
├── Arduino/
│   └── GSMClient/
│       └── GSMClient.ino
├── django/
│   └── smart_trails/
│       ├── api/              # REST endpoints
│       ├── sensors/          # Sensor reading models
│       ├── stations/         # Station metadata
│       └── smart_trails/     # Django settings
└── iOS/
    └── SmartTrails/
        ├── SmartTrails/              # iOS app
        │   ├── Views/
        │   ├── ViewModels/
        │   ├── Models/
        │   └── Services/
        └── SmartTrails Watch App/    # watchOS app
            ├── Views/
            ├── ViewModels/
            ├── Models/
            └── Services/
```
