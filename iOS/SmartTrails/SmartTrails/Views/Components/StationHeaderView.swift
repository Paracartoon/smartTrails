//
//  StationHeaderView.swift
//  SmartTrails
//
//  Created by Kate Dmitrieva on 30/11/25.
//

import SwiftUI

struct StationHeaderView: View {
   let data: StationData

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Station ID
            Text(data.stationId.replacingOccurrences(of: "-", with: " ").capitalized)
               .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(Theme.textOnColor)

            // Time
            HStack(spacing: 4) {
               Image(systemName: "clock")
                    .font(.caption)
                Text(DateFormatters.humanReadable.string(from: data.timestamp))
                    .font(.caption)
            }
            .foregroundColor(Theme.textOnColorSecondary)

            Divider()
               .background(Theme.textOnColorSecondary.opacity(0.3))

            // Location info
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 4) {
                   Image(systemName: "map")
                        .font(.caption)
                    Text(data.location.trailName)
                        .font(.subheadline)
                        .fontWeight(.medium)
                }
                .foregroundColor(Theme.textOnColor)

                HStack(spacing: 16) {
                   HStack(spacing: 4) {
                        Image(systemName: "location")
                            .font(.caption2)
                        Text(String(format: "%.4f, %.4f", data.location.latitude, data.location.longitude))
                            .font(.caption)
                    }

                   HStack(spacing: 4) {
                        Image(systemName: "arrow.up.forward")
                            .font(.caption2)
                        Text("\(Int(data.location.altitude))m")
                            .font(.caption)
                    }
                }
                .foregroundColor(Theme.textOnColorSecondary)
            }
        }
       .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(Theme.headerColor)
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.15), radius: 4, x: 0, y: 2)
    }
}

#Preview {
   StationHeaderView(data: NetworkService.mockStationData)
        .padding()
}
