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
   static let shared = NetworkService()

    private let baseURL = "https://smart-trails.com/api/v1"

    private let decoder: JSONDecoder = {
       let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()

   private init() {}

    // MARK: - Public API

    func fetchStationData(stationId: String = "mombarone-san-carlo") async throws -> StationData {
       guard let url = URL(string: "\(baseURL)/stations/\(stationId)/data/") else {
            throw NetworkError.invalidURL
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData

        let (data, response) = try await URLSession.shared.data(for: request)

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
}
