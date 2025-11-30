//
//  DateFormatters.swift
//  SmartTrails
//
//  Created by Kate Dmitrieva on 11/11/25.
//

import Foundation

enum DateFormatters {
   /// like  "Nov 22, 2024 at 2:30 PM"
    static let humanReadable: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
       return formatter
    }()

   /// decoder for parsing API times
    static let iso8601: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        return formatter
    }()

   /// Relative time format: "5 minutes ago"
    static let relative: RelativeDateTimeFormatter = {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .full
        return formatter
    }()
}
