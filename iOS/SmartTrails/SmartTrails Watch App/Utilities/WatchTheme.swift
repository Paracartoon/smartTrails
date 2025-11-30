//
//  WatchTheme.swift
//  SmartTrails Watch App
//
//  Created by Kate Dmitrieva on 30/11/25.
//

import SwiftUI

enum WatchTheme {
   static let headerColor = Color(red: 0.176, green: 0.216, blue: 0.282)

    static let atmosphericColor = Color(red: 0.118, green: 0.227, blue: 0.373)
    static let lightColor = Color(red: 0.706, green: 0.325, blue: 0.035)
    static let soilColor = Color(red: 0.365, green: 0.251, blue: 0.216)
    static let airQualityColor = Color(red: 0.067, green: 0.369, blue: 0.349)
    static let precipitationColor = Color(red: 0.047, green: 0.290, blue: 0.431)
   static let trailActivityColor = Color(red: 0.239, green: 0.220, blue: 0.208)

    // MARK: - Background
    static let appBackground = Color.black

    // MARK: - Text - basically always white

    static let textOnColor = Color.white

    /// Secondary text on colored backgrounds - light gray (#E5E7EB)
    static let textOnColorSecondary = Color(red: 0.898, green: 0.906, blue: 0.922)

    /// Danger color - orange now (TODO: replace with red but watch ios too)
    static let danger = Color(red: 0.918, green: 0.345, blue: 0.047)

   // MARK: - Section Color Helper

    static func sectionColor(for section: WatchSensorSection) -> Color {
        switch section {
        case .atmospheric:
            return atmosphericColor
       case .light:
            return lightColor
        case .soil:
            return soilColor
        case .airQuality:
            return airQualityColor
       case .precipitation:
            return precipitationColor
        case .trailActivity:
            return trailActivityColor
        }
    }

   static func icon(for section: WatchSensorSection) -> String {
        switch section {
        case .atmospheric:
            return "cloud.fill"
        case .light:
           return "sun.max.fill"
        case .soil:
            return "leaf.fill"
        case .airQuality:
            return "aqi.medium"
        case .precipitation:
           return "drop.fill"
        case .trailActivity:
            return "figure.walk"
        }
    }
}

enum WatchSensorSection: String, CaseIterable {
   case atmospheric = "Atmospheric"
    case light = "Light"
    case soil = "Soil"
    case airQuality = "Air Quality"
    case precipitation = "Precipitation"
    case trailActivity = "Activity"
}
