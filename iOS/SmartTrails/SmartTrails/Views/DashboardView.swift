//
//  DashboardView.swift
//  SmartTrails
//
//  Created by Kate Dmitrieva on 30/11/25.
//

import SwiftUI

struct DashboardView: View {
    @EnvironmentObject var viewModel: DashboardViewModel
    @ObservedObject private var notificationService = NotificationService.shared
    @State private var showNotifications = false

    var body: some View {
        NavigationStack {
           ZStack {
                // App background color (sandy/warm)
                Theme.appBackground
                    .ignoresSafeArea()

                if let data = viewModel.stationData {
                   ScrollView {
                        VStack(spacing: 16) {
                            // Station Header
                            StationHeaderView(data: data)

                            // Atmospheric
                           SectionCard(section: .atmospheric) {
                                MetricRow(
                                    label: "Temperature",
                                    value: String(format: "%.1f", data.sensors.atmospheric.temperature),
                                    unit: "°C",
                                    isDangerous: data.sensors.atmospheric.temperatureIsDangerous
                                )
                               MetricRow(
                                    label: "Humidity",
                                    value: String(format: "%.1f", data.sensors.atmospheric.humidity),
                                    unit: "%",
                                    isDangerous: data.sensors.atmospheric.humidityIsDangerous
                                )
                                MetricRow(
                                    label: "Pressure",
                                    value: String(format: "%.1f", data.sensors.atmospheric.pressure),
                                    unit: "hPa",
                                    isDangerous: data.sensors.atmospheric.pressureIsDangerous
                                )
                            }

                           // Light
                            SectionCard(section: .light) {
                                MetricRow(
                                    label: "UV Index",
                                    value: String(format: "%.1f", data.sensors.light.uvIndex),
                                    isDangerous: data.sensors.light.uvIndexIsDangerous
                                )
                               MetricRow(
                                    label: "Light Intensity",
                                    value: formatLux(data.sensors.light.lux),
                                    unit: "lux",
                                    isDangerous: data.sensors.light.luxIsDangerous
                                )
                            }

                            // Soil
                            SectionCard(section: .soil) {
                               MetricRow(
                                    label: "Moisture",
                                    value: String(format: "%.1f", data.sensors.soil.moisturePercent),
                                    unit: "%",
                                    isDangerous: data.sensors.soil.moisturePercentIsDangerous
                                )
                            }

                           //  Qalita aria
                            SectionCard(section: .airQuality) {
                                MetricRow(
                                    label: "CO₂",
                                    value: String(format: "%.0f", data.sensors.airQuality.co2Ppm),
                                    unit: "ppm",
                                    isDangerous: data.sensors.airQuality.co2PpmIsDangerous
                                )
                            }

                           // Precipitation
                            SectionCard(section: .precipitation) {
                                BooleanMetricRow(
                                    label: "Currently Raining",
                                    value: data.sensors.precipitation.isRaining,
                                    isDangerous: data.sensors.precipitation.isRainingIsDangerous
                                )
                               BooleanMetricRow(
                                    label: "Rain in Last Hour",
                                    value: data.sensors.precipitation.rainDetectedLastHour,
                                    isDangerous: data.sensors.precipitation.rainDetectedLastHourIsDangerous
                                )
                            }

                            // Trail Activity
                            SectionCard(section: .trailActivity) {
                               MetricRow(
                                    label: "Motion Detected",
                                    value: "\(data.sensors.trailActivity.motionCount)",
                                    unit: "times",
                                    isDangerous: data.sensors.trailActivity.motionCountIsDangerous
                                )
                                MetricRow(
                                    label: "Period",
                                    value: "\(data.sensors.trailActivity.periodMinutes)",
                                    unit: "min"
                                )
                            }
                        }
                       .padding()
                    }
                    .refreshable {
                        await viewModel.refresh()
                    }
               } else if let error = viewModel.error {
                    errorView(error: error)
                }

                // Blocking overlay during refresh
               // TODO: do we want to block UI?
                if viewModel.isRefreshing {
                   refreshOverlay
                }
            }
            .navigationTitle("SmartTrails")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    notificationBellButton
                }
            }
            .navigationDestination(isPresented: $showNotifications) {
                NotificationsView()
            }
            .onChange(of: notificationService.shouldNavigateToNotifications) { _, shouldNavigate in
                if shouldNavigate {
                    showNotifications = true
                    notificationService.shouldNavigateToNotifications = false
                }
            }
        }
    }

    private var notificationBellButton: some View {
        Button {
            showNotifications = true
        } label: {
            ZStack(alignment: .topTrailing) {
                Image(systemName: "bell.fill")
                    .font(.system(size: 18))
                    .foregroundColor(Theme.textPrimary)

                if notificationService.unreadCount > 0 {
                    Text(notificationService.unreadCount > 99 ? "99+" : "\(notificationService.unreadCount)")
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(.white)
                        .padding(.horizontal, 5)
                        .padding(.vertical, 2)
                        .background(Theme.danger)
                        .clipShape(Capsule())
                        .offset(x: 8, y: -8)
                }
            }
        }
    }


    private var refreshOverlay: some View {
        ZStack {
            Color.black.opacity(0.3)
               .ignoresSafeArea()

            VStack(spacing: 16) {
                ProgressView()
                    .scaleEffect(1.5)
                    .tint(.white)

               Text("Refreshing...")
                    .font(.subheadline)
                    .foregroundColor(.white)
            }
            .padding(24)
            .background(.ultraThinMaterial)
            .cornerRadius(12)
        }
    }

   private func errorView(error: NetworkError) -> some View {
        VStack(spacing: 16) { //14
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 50))
                .foregroundColor(.orange)

           Text("Unable to Load Data")
                .font(.headline)

            Text(error.localizedDescription)
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)

//            Button {
//               Task {
//                   await viewModel.isLoading
//                }
//            }

            Button {
               Task {
                    await viewModel.loadInitialData()
                }
            } label: {
                Label("Retry", systemImage: "arrow.clockwise")
                    .font(.headline)
                    .padding(.horizontal, 24)
                    .padding(.vertical, 12)
                   .background(Theme.primary)
                    .foregroundColor(.white)
                    .cornerRadius(8)
            }
        }
        .padding()
    }

    // MARK: - Helpers

   private func formatLux(_ lux: Double) -> String {
        if lux >= 1000 {
            return String(format: "%.0fk", lux / 1000)
        }
        return String(format: "%.0f", lux)
    }
}


