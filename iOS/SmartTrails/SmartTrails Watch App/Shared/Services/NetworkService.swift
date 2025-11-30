//
//  NetworkService.swift
//  SmartTrails Watch App
//
//  Created by Kate Dmitrieva on 30/11/25.
//

import Foundation

// MARK: - Network Errors

enum NetworkError: Error, LocalizedError {
   case invalidURL
    case networkFailure(Error)
    case decodingError(Error)
    case serverError(statusCode: Int)
    case noData

    var errorDescription: String? {
       switch self {
        case .invalidURL:
            return "Invalid URL"
        case .networkFailure(let error):
            return "Network error: \(error.localizedDescription)"
        case .decodingError(let error):
           return "Failed to parse data: \(error.localizedDescription)"
        case .serverError(let statusCode):
            return "Server error: \(statusCode)"
        case .noData:
            return "No data received"
        }
    }
}

// MARK: - Network Service

final class NetworkService {
   static let shared = NetworkService()

    // TODO: Replace with actual API endpoint
    private let baseURL = "https://api.example.com"

   private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()

    private init() {}

   // MARK: - Public API

    /// Fetches station data from the API
    /// Currently returns mock data for development
    func fetchStationData(stationId: String = "mombarone-san-carlo") async throws -> StationData {
        // TODO: Replace with actual API call when endpoint is ready
       // Simulate network delay
        try await Task.sleep(nanoseconds: 1_000_000_000) // 1 second delay

        return Self.mockStationData
    }

   // MARK: - Mock Data

    static let mockStationData = StationData(
        stationId: "mombarone-san-carlo",
        timestamp: Date(),
        location: Location(
           latitude: 45.5615,
            longitude: 8.0573,
            altitude: 1250,
            trailName: "Sentiero Graglia"
        ),
        sensors: Sensors(
           atmospheric: Atmospheric(
                temperature: 12.5,
                temperatureIsDangerous: false,
                humidity: 65.0,
                humidityIsDangerous: false,
               pressure: 875.3,
                pressureIsDangerous: false
            ),
            light: Light(
                uvIndex: 3.2,
               uvIndexIsDangerous: false,
                lux: 45000,
                luxIsDangerous: false
            ),
            soil: Soil(
                moisturePercent: 45.5,
               moisturePercentIsDangerous: false
            ),
            airQuality: AirQuality(
                co2Ppm: 420,
                co2PpmIsDangerous: false
            ),
           precipitation: Precipitation(
                isRaining: false,
                isRainingIsDangerous: false,
                rainDetectedLastHour: true,
                rainDetectedLastHourIsDangerous: false
            ),
           trailActivity: TrailActivity(
                motionCount: 12,
                motionCountIsDangerous: false,
                periodMinutes: 60
            )
        )
    )
}
