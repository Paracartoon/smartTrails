//
//  DashboardViewModel.swift
//  SmartTrails
//
//  Created by Kate Dmitrieva on 28/11/25.
//

import Foundation
import Combine

@MainActor
final class DashboardViewModel: ObservableObject {
    // MARK: - Observable Properties

    @Published private(set) var stationData: StationData?
    @Published private(set) var isLoading = true


    @Published private(set) var isRefreshing = false
    @Published private(set) var error: NetworkError?

    // MARK: - Private Properties

    private let networkService: NetworkService
    // replace
    nonisolated(unsafe) private var refreshTimer: Timer?
    /// refresh every 5 mins (change to 1? or 20)
    private let refreshInterval: TimeInterval = 300

  // MARK: - Init

    init(networkService: NetworkService = .shared) {
        self.networkService = networkService
    }

    // MARK: - Public apis

    /// Loads initial data when app starts
    func loadInitialData() async {
        isLoading = true
        error = nil

        await fetchData()

        isLoading = false
        startAutoRefresh()
    }

   /// Manual refresh via pull-to-refresh
    func refresh() async {
        print("REFRESH CALLED")
        guard !isRefreshing else {
            print("Already refreshing, skipping")
            return
        }

        isRefreshing = true
        error = nil

        await withCheckedContinuation { continuation in
            Task {
                await fetchData()
                continuation.resume()
            }
        }

        isRefreshing = false
    }

    /// Starts automatic refresh every x minutes (5)
   func startAutoRefresh() {
        stopAutoRefresh()

        refreshTimer = Timer.scheduledTimer(withTimeInterval: refreshInterval, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
               await self?.refresh()
            }
        }
    }

   /// Stops automatic refresh (e.g., when app goes to background)
    func stopAutoRefresh() {
        refreshTimer?.invalidate()
        refreshTimer = nil
    }

    // MARK: - Private Methods

    private func fetchData() async {
       do {
            let newData = try await networkService.fetchStationData()
            print("1 -->>> Fetched data with timestamp", newData.timestamp)
           stationData = newData
            error = nil

        } catch let networkError as NetworkError {
            print("Fetch error: \(networkError)")
            self.error = networkError

       } catch {
            print("Fetch error: \(error)")
            self.error = .networkFailure(error)
        }
    }

   // MARK: - Computed properties and helpers

    /// Formatted time for display
    var formattedTimestamp: String {
        guard let timestamp = stationData?.timestamp else { return "--" }
        return DateFormatters.humanReadable.string(from: timestamp)
    }

    /// Station title for navigation bar
   var stationTitle: String {
        stationData?.stationId.replacingOccurrences(of: "-", with: " ").capitalized ?? "SmartTrails"
    }

    /// Location display string
    var locationDescription: String {
       guard let location = stationData?.location else { return "--" }
        return "\(location.trailName) • \(Int(location.altitude))m"
    }

    /// Coordinates display string
    var coordinatesDescription: String {
       guard let location = stationData?.location else { return "--" }
        return String(format: "%.4f, %.4f", location.latitude, location.longitude)
    }
}
