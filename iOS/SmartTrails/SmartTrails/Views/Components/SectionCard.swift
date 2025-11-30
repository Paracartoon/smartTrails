//
//  SectionCard.swift
//  SmartTrails
//
//  Created by Kate Dmitrieva on 30/11/25.
//

import SwiftUI

struct SectionCard<Content: View>: View {
   let section: SensorSection
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label {
               Text(section.rawValue)
                    .font(.headline)
                    .foregroundColor(Theme.textOnColor)
            } icon: {
                Image(systemName: Theme.icon(for: section))
                    .foregroundColor(Theme.textOnColor)
            }

           VStack(spacing: 8) {
                content
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Theme.sectionColor(for: section))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.15), radius: 4, x: 0, y: 2)
    }
}

#Preview {
   VStack(spacing: 16) {
        SectionCard(section: .atmospheric) {
            MetricRow(label: "Temperature", value: "12.5", unit: "°C")
            MetricRow(label: "Humidity", value: "65", unit: "%")
            MetricRow(label: "Pressure", value: "875.3", unit: "hPa")
        }

       SectionCard(section: .light) {
            MetricRow(label: "UV Index", value: "11.0", isDangerous: true)
            MetricRow(label: "Light", value: "45000", unit: "lux")
        }
    }
   .padding()
}
