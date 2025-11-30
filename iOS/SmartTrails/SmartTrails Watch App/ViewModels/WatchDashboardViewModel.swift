//
//  WatchDashboardViewModel.swift
//  SmartTrails Watch App
//
//  Created by Kate Dmitrieva on 30/11/25.
//

import Foundation
import Combine

@MainActor
final class WatchDashboardViewModel: ObservableObject {
    // MARK: - Observables

    @Published private(set) var stationData: StationData?
    @Published private(set) var isLoading = true
    @Published private(set) var isRefreshing = false

    // can  make public?
   @Published private(set) var error: NetworkError?

    // MARK: - Private Properties

    private let networkService: NetworkService

    //private var timer: Timer?
    nonisolated(unsafe) private var refreshTimer: Timer?

    private let refreshInterval: TimeInterval = 300 // 5 minutes

  // MARK: - Init

    init(networkService: NetworkService = .shared) {
        self.networkService = networkService
    }

    // MARK: - Public Methods

   func loadInitialData() async {
        isLoading = true
        error = nil

        await fetchData()

        isLoading = false

       print("LOADING, REFRESHING!")
       startAutoRefresh()
    }

    func refresh() async {
        guard !isRefreshing else { return }

        isRefreshing = true
        print("Set err to nil _______")
        error = nil

        await fetchData()

       isRefreshing = false
    }

   func startAutoRefresh() {
        stopAutoRefresh()

        refreshTimer = Timer.scheduledTimer(withTimeInterval: refreshInterval, repeats: true) { [weak self] _ in
          Task { @MainActor [weak self] in
                await self?.refresh()
            }
        }
    }

    func stopAutoRefresh() {
       refreshTimer?.invalidate()
        print("Set timer to nil _______")
        refreshTimer = nil
    }

    // MARK: - Private Methods

    private func fetchData() async {
        do {
          stationData = try await networkService.fetchStationData()
            error = nil
        } catch let networkError as NetworkError {
            print("Set err to actual error _______", networkError)
           self.error = networkError
        } catch {
            self.error = .networkFailure(error)
        }
    }
}
