//
//  WatchMetricRow.swift
//  SmartTrails Watch App
//
//  Created by Kate Dmitrieva on 30/11/25.
//

import SwiftUI

struct WatchMetricRow: View {
   let label: String
    let value: String
    let unit: String
    let isDangerous: Bool

    init(label: String, value: String, unit: String = "", isDangerous: Bool = false) {
       self.label = label
        self.value = value
        self.unit = unit
        self.isDangerous = isDangerous
    }

    var body: some View {
        HStack {
           Text(label)
                .font(.caption2)
                .foregroundColor(WatchTheme.textOnColorSecondary)
                .lineLimit(1)

            Spacer()

           HStack(spacing: 1) {
                Text(value)
                    .font(.caption)
                    .fontWeight(.bold)
                    .foregroundColor(isDangerous ? WatchTheme.danger : WatchTheme.textOnColor)

               if !unit.isEmpty {
                    Text(unit)
                        .font(.system(size: 9))
                        .fontWeight(.medium)
                        .foregroundColor(isDangerous ? WatchTheme.danger.opacity(0.8) : WatchTheme.textOnColorSecondary)
                }
            }
        }
    }
}

struct WatchBooleanMetricRow: View {
   let label: String
    let value: Bool
    let isDangerous: Bool

    init(label: String, value: Bool, isDangerous: Bool = false) {
        self.label = label
        self.value = value
        self.isDangerous = isDangerous
    }

   // bolean metric row body
    var body: some View {
        HStack {
            Text(label)
                .font(.caption2)
               .foregroundColor(WatchTheme.textOnColorSecondary)
                .lineLimit(1)

            Spacer()

            HStack(spacing: 2) {
               Image(systemName: value ? "checkmark.circle.fill" : "xmark.circle.fill")
                    .font(.system(size: 10))
                    .foregroundColor(isDangerous ? WatchTheme.danger : (value ? .green.opacity(0.9) : WatchTheme.textOnColorSecondary))

                Text(value ? "Yes" : "No")
                    .font(.caption)
                    .fontWeight(.bold)
                    .foregroundColor(isDangerous ? WatchTheme.danger : WatchTheme.textOnColor)
            }
        }
    }
}

struct WatchSectionHeader: View {
   let section: WatchSensorSection

    var body: some View {
        HStack(spacing: 4) {
           Image(systemName: WatchTheme.icon(for: section))
                .font(.caption2)
                .foregroundColor(WatchTheme.textOnColor)

            Text(section.rawValue)
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(WatchTheme.textOnColor)

            Spacer()
        }
       .padding(.vertical, 6)
        .padding(.horizontal, 8)
        .background(WatchTheme.sectionColor(for: section))
        .cornerRadius(6)
    }
}

#Preview("Metric Rows") {
   VStack {
        WatchSectionHeader(section: .atmospheric)
        WatchMetricRow(label: "Temp", value: "12.5", unit: "°C")
        WatchMetricRow(label: "UV", value: "11.0", isDangerous: true)
        WatchBooleanMetricRow(label: "Rain", value: true, isDangerous: true)
    }
}
