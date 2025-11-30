//
//  WatchDashboardView.swift
//  SmartTrails Watch App
//
//  Created by Kate Dmitrieva on 30/11/25.
//

import SwiftUI

struct WatchDashboardView: View {
   @EnvironmentObject var viewModel: WatchDashboardViewModel

    var body: some View {
        NavigationStack {
           ZStack {
                // Background color - always black
               // no light/dark mode on the watch!
                WatchTheme.appBackground
                    .ignoresSafeArea()

                if let data = viewModel.stationData {
                   ScrollView {
                        VStack(alignment: .leading, spacing: 6) {
                            headerSection(data: data)

                            // Atmospheric data
                           WatchSectionHeader(section: .atmospheric)
                            WatchMetricRow(
                                label: "Temp",
                                value: String(format: "%.1f", data.sensors.atmospheric.temperature),
                                unit: "°C",
                                isDangerous: data.sensors.atmospheric.temperatureIsDangerous
                            )
                           WatchMetricRow(
                                label: "Humidity",
                                value: String(format: "%.0f", data.sensors.atmospheric.humidity),
                                unit: "%",
                                isDangerous: data.sensors.atmospheric.humidityIsDangerous
                            )
                            WatchMetricRow(
                                label: "Pressure",
                                value: String(format: "%.0f", data.sensors.atmospheric.pressure),
                                unit: "hPa",
                                isDangerous: data.sensors.atmospheric.pressureIsDangerous
                            )

                           // Light
                            WatchSectionHeader(section: .light)
                            WatchMetricRow(
                                label: "UV Index",
                                value: String(format: "%.1f", data.sensors.light.uvIndex),
                                isDangerous: data.sensors.light.uvIndexIsDangerous
                            )
                           WatchMetricRow(
                                label: "Lux",
                                value: formatLux(data.sensors.light.lux),
                                isDangerous: data.sensors.light.luxIsDangerous
                            )

                            // Soil
                            WatchSectionHeader(section: .soil)
                            WatchMetricRow(
                                label: "Moisture",
                                value: String(format: "%.1f", data.sensors.soil.moisturePercent),
                                unit: "%",
                                isDangerous: data.sensors.soil.moisturePercentIsDangerous
                            )

                           // Air
                            WatchSectionHeader(section: .airQuality)
                            WatchMetricRow(
                                label: "CO₂",
                                value: String(format: "%.0f", data.sensors.airQuality.co2Ppm),
                                unit: "ppm",
                                isDangerous: data.sensors.airQuality.co2PpmIsDangerous
                            )

                           // Precipitation
                            WatchSectionHeader(section: .precipitation)
                            WatchBooleanMetricRow(
                                label: "Raining",
                                value: data.sensors.precipitation.isRaining,
                                isDangerous: data.sensors.precipitation.isRainingIsDangerous
                            )
                           WatchBooleanMetricRow(
                                label: "Rain 1hr",
                                value: data.sensors.precipitation.rainDetectedLastHour,
                                isDangerous: data.sensors.precipitation.rainDetectedLastHourIsDangerous
                            )

                            // Trail Activity
                            WatchSectionHeader(section: .trailActivity)
                            WatchMetricRow(
                                label: "Motion",
                                value: "\(data.sensors.trailActivity.motionCount)",
                                unit: "×",
                                isDangerous: data.sensors.trailActivity.motionCountIsDangerous
                            )
                            WatchMetricRow(
                                label: "Period",
                                value: "\(data.sensors.trailActivity.periodMinutes)",
                                unit: "min"
                            )
                        }
                       .padding(.horizontal, 4)
                    }
                    .refreshable {
                        await viewModel.refresh()
                    }
               } else if let error = viewModel.error {
                    errorView(error: error)
                }

                // Refresh overlay
                if viewModel.isRefreshing {
                   refreshOverlay
                }
            }
            .navigationTitle("SmartTrails")
            .navigationBarTitleDisplayMode(.inline)
        }
    }

   // MARK: - Subviews

    private func headerSection(data: StationData) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(data.location.trailName)
                .font(.caption)
//                .fontWeight(.bold)
                .fontWeight(.semibold)
                .foregroundColor(WatchTheme.textOnColor)
                .lineLimit(1)

            Text("\(Int(data.location.altitude))m")
                .font(.caption2)
                .foregroundColor(WatchTheme.textOnColorSecondary)
        }
       .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.vertical, 6)
        .padding(.horizontal, 8)
        .background(WatchTheme.headerColor)
        .cornerRadius(6)
    }

   private var refreshOverlay: some View {
        ZStack {
            Color.black.opacity(0.4)
//                .opacity(0.4)
                .ignoresSafeArea()

            ProgressView()
               .tint(.white)
        }
    }

   private func errorView(error: NetworkError) -> some View {
        VStack(spacing: 8) {
            Image(systemName: "exclamationmark.triangle")
                .font(.title3)
                .foregroundColor(WatchTheme.danger)

           Text("Error")
                .font(.caption)
                .fontWeight(.semibold)

            Button {
               Task {
                    await viewModel.loadInitialData()
                }
            } label: {
//                Label("Try again!", systemImage: "arrow.clockwise")
//                    .font(.caption2)
                Label("Retry", systemImage: "arrow.clockwise")
                    .font(.caption2)
            }
        }
    }

   // MARK: - Helpers

    private func formatLux(_ lux: Double) -> String {
        if lux >= 1000 {
            return String(format: "%.0fk", lux / 1000)
        }
       return String(format: "%.0f", lux)
    }
}

