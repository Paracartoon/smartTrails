//
//  MetricRow.swift
//  SmartTrails
//
//  Created by Kate Dmitrieva on 30/11/25.
//

import SwiftUI

struct MetricRow: View {
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
                .font(.subheadline)
                .foregroundColor(Theme.textOnColorSecondary)

            Spacer()

           HStack(spacing: 2) {
                Text(value)
                    .font(.callout)
                    .fontWeight(.bold)
                    .foregroundColor(isDangerous ? Theme.danger : Theme.textOnColor)

               if !unit.isEmpty {
                    Text(unit)
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundColor(isDangerous ? Theme.danger.opacity(0.8) : Theme.textOnColorSecondary)
                }
            }
        }
    }
}

struct BooleanMetricRow: View {
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
                .font(.subheadline)
               .foregroundColor(Theme.textOnColorSecondary)

            Spacer()

            HStack(spacing: 4) {
               Image(systemName: value ? "checkmark.circle.fill" : "xmark.circle.fill")
                    .font(.callout)
                    .foregroundColor(isDangerous ? Theme.danger : (value ? .green.opacity(0.9) : Theme.textOnColorSecondary))

                Text(value ? "Yes" : "No")
                    .font(.callout)
                    .fontWeight(.bold)
                    .foregroundColor(isDangerous ? Theme.danger : Theme.textOnColor)
            }
        }
    }
}

#Preview("Normal Metric") {
    VStack {
       MetricRow(label: "Temperature", value: "12.5", unit: "°C")
        MetricRow(label: "Humidity", value: "65", unit: "%")
    }
    .padding()
}

#Preview("Dangerous Metric") {
    VStack {
       MetricRow(label: "Temperature", value: "38.5", unit: "°C", isDangerous: true)
        MetricRow(label: "UV Index", value: "11.0", isDangerous: true)
    }
    .padding()
}

#Preview("Boolean Metrics") {
    VStack {
       BooleanMetricRow(label: "Is Raining", value: false)
        BooleanMetricRow(label: "Is Raining", value: true, isDangerous: true)
    }
    .padding()
}
