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
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let dateString = try container.decode(String.self)

            // Try ISO8601 with fractional seconds first
            let formatterWithFractional = ISO8601DateFormatter()
            formatterWithFractional.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            if let date = formatterWithFractional.date(from: dateString) {
                return date
            }

            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime]
            if let date = formatter.date(from: dateString) {
                return date
            }

            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "Cannot decode date: \(dateString)"
            )
        }
        return decoder
    }()

   private init() {}

    // MARK: - Public API

    func registerDeviceToken(token: String, platform: String, bundleId: String) {
        guard let url = URL(string: "\(baseURL)/notifications/register/") else {
            print("1111 wrong url")
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "token": token,
            "platform": platform,
            "bundle_id": bundleId
        ]

        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("failed --- 1111 registration", error)
                return
            }

            if let httpResponse = response as? HTTPURLResponse {
                if httpResponse.statusCode == 201 || httpResponse.statusCode == 200 {
                    print("YES!!!")
                } else {
                    print("NO --- error: ", httpResponse.statusCode)
                }
            }
        }.resume()
    }

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
