//
//  StationData.swift
//  SmartTrails
//
//  Created by Kate Dmitrieva on 30/11/25.
//

import Foundation

// MARK: - Root Model

struct StationData: Codable, Identifiable {
   let stationId: String
    let timestamp: Date
    let location: Location
    let sensors: Sensors

    var id: String { stationId }

   enum CodingKeys: String, CodingKey {
        case stationId = "station_id"
        case timestamp
        case location
        case sensors
    }
}

// MARK: - Location

struct Location: Codable {
   let latitude: Double
    let longitude: Double
    let altitude: Double
    let trailName: String

    enum CodingKeys: String, CodingKey {
       case latitude
        case longitude
        case altitude
        case trailName = "trail_name"
    }
}

// MARK: - Sensors Container

struct Sensors: Codable {
   let atmospheric: Atmospheric
    let light: Light
    let soil: Soil
    let airQuality: AirQuality
    let precipitation: Precipitation
    let trailActivity: TrailActivity

   enum CodingKeys: String, CodingKey {
        case atmospheric
        case light
       case soil
        case airQuality = "air_quality"
        case precipitation
        case trailActivity = "trail_activity"
    }
}

// MARK: - Sensor Types

struct Atmospheric: Codable {
   let temperature: Double
    let temperatureIsDangerous: Bool
    let humidity: Double
    let humidityIsDangerous: Bool
    let pressure: Double
    let pressureIsDangerous: Bool

   enum CodingKeys: String, CodingKey {
        case temperature
        case temperatureIsDangerous = "temperature_is_dangerous"
        case humidity
        case humidityIsDangerous = "humidity_is_dangerous"
       case pressure
        case pressureIsDangerous = "pressure_is_dangerous"
    }
}

struct Light: Codable {
   let uvIndex: Double
    let uvIndexIsDangerous: Bool
    let lux: Double
    let luxIsDangerous: Bool

    enum CodingKeys: String, CodingKey {
       case uvIndex = "uv_index"
        case uvIndexIsDangerous = "uv_index_is_dangerous"
        case lux
        case luxIsDangerous = "lux_is_dangerous"
    }
}

struct Soil: Codable {
   let moisturePercent: Double
    let moisturePercentIsDangerous: Bool

    enum CodingKeys: String, CodingKey {
        case moisturePercent = "moisture_percent"
        case moisturePercentIsDangerous = "moisture_percent_is_dangerous"
    }
}

struct AirQuality: Codable {
   let co2Ppm: Double
    let co2PpmIsDangerous: Bool

    enum CodingKeys: String, CodingKey {
        case co2Ppm = "co2_ppm"
        case co2PpmIsDangerous = "co2_ppm_is_dangerous"
    }
}

struct Precipitation: Codable {
   let isRaining: Bool
    let isRainingIsDangerous: Bool
    let rainDetectedLastHour: Bool
    let rainDetectedLastHourIsDangerous: Bool

    enum CodingKeys: String, CodingKey {
        case isRaining = "is_raining"
       case isRainingIsDangerous = "is_raining_is_dangerous"
        case rainDetectedLastHour = "rain_detected_last_hour"
        case rainDetectedLastHourIsDangerous = "rain_detected_last_hour_is_dangerous"
    }
}

struct TrailActivity: Codable {
   let motionCount: Int
    let motionCountIsDangerous: Bool
    let periodMinutes: Int

    enum CodingKeys: String, CodingKey {
        case motionCount = "motion_count"
       case motionCountIsDangerous = "motion_count_is_dangerous"
        case periodMinutes = "period_minutes"
    }
}
