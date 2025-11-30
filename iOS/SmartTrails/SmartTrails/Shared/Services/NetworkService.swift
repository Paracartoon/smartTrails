//
//  NetworkService.swift
//  SmartTrails
//
//  Created by Kate Dmitrieva on 28/11/25.
//

import Foundation

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




final class NetworkService {
    // using singleton for now
   static let shared = NetworkService()

    // TODO: make get endpoint!!!! this one is post
    private let baseURL = "https://smart-trails.com/v1/api/"

    private let decoder: JSONDecoder = {
       let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()

   private init() {}

    // MARK: - Public API

    /// Fetch station data from the API
   func fetchStationData(stationId: String = "mombarone-san-carlo") async throws -> StationData {
        // TODO: Replace with actual API call when endpoint is ready
        // Simulate network delay - if needed
        try await Task.sleep(nanoseconds: 1_000_000_000)

       return Self.mockStationData
    }

    /*
    func fetchStationDataFromAPI(stationId: String) async throws -> StationData {
       guard let url = URL(string: "\(baseURL)/stations/\(stationId)/data") else {
            throw NetworkError.invalidURL
        }

        let (data, response) = try await URLSession.shared.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse else {
           throw NetworkError.noData
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.serverError(statusCode: httpResponse.statusCode)
        }

        do {
           return try decoder.decode(StationData.self, from: data)
        } catch {
            throw NetworkError.decodingError(error)
        }
    }
   */

 // TEMP! (or move to mockups)

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


    static let mockDangerousStationData = StationData(
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
                temperature: 38.5,
               temperatureIsDangerous: true,
                humidity: 95.0,
                humidityIsDangerous: true,
                pressure: 875.3,
                pressureIsDangerous: false
            ),
           light: Light(
                uvIndex: 11.0,
                uvIndexIsDangerous: true,
                lux: 120000,
                luxIsDangerous: true
            ),
           soil: Soil(
                moisturePercent: 5.0,
                moisturePercentIsDangerous: true
            ),
            airQuality: AirQuality(
               co2Ppm: 1500,
                co2PpmIsDangerous: true
            ),
            precipitation: Precipitation(
                isRaining: true,
               isRainingIsDangerous: true,
                rainDetectedLastHour: true,
                rainDetectedLastHourIsDangerous: false
            ),
            trailActivity: TrailActivity(
                motionCount: 0,
               motionCountIsDangerous: false,
                periodMinutes: 60
            )
        )
    )
}
