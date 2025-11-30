//
//  Theme.swift
//  SmartTrails
//
//  Created by Kate Dmitrieva on 30/11/25.
//

import SwiftUI

enum Theme {
   // MARK: - Sections

    static let headerColor = Color(red: 0.176, green: 0.216, blue: 0.282)
    static let atmosphericColor = Color(red: 0.118, green: 0.227, blue: 0.373)
    static let lightColor = Color(red: 0.706, green: 0.325, blue: 0.035)
    static let soilColor = Color(red: 0.365, green: 0.251, blue: 0.216)
    static let airQualityColor = Color(red: 0.067, green: 0.369, blue: 0.349)
    static let precipitationColor = Color(red: 0.047, green: 0.290, blue: 0.431)

    static let trailActivityColor = Color(red: 0.239, green: 0.220, blue: 0.208)

    // MARK: - Backgrounds

    static let appBackground = Color(red: 0.839, green: 0.827, blue: 0.808)

    // MARK: - Text Colors

    static let textOnColor = Color.white

    static let textOnColorSecondary = Color(red: 0.898, green: 0.906, blue: 0.922)
    static let textPrimary = Color(red: 0.176, green: 0.216, blue: 0.282)
    static let textSecondary = textPrimary.opacity(0.7)

   // MARK: - Accents

    static let primary = atmosphericColor
    static let slateGray = headerColor
    static let danger = Color(red: 0.918, green: 0.345, blue: 0.047)

    // MARK: - Helpers

   static func sectionColor(for section: SensorSection) -> Color {
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

   static func icon(for section: SensorSection) -> String {
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

enum SensorSection: String, CaseIterable {
   case atmospheric = "Atmospheric"
    case light = "Light"
    case soil = "Soil"
    case airQuality = "Air Quality"
    case precipitation = "Precipitation"
    case trailActivity = "Trail Activity"
}
