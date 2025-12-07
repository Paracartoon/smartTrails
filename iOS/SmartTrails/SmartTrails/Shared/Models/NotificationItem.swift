//
//  NotificationItem.swift
//  SmartTrails
//
//  Created by Kate Dmitrieva on 07/12/25.
//

import Foundation

struct NotificationItem: Identifiable, Codable, Equatable {
    let id: UUID
    let title: String
    let body: String
    let timestamp: Date
    var isRead: Bool
    let stationId: String?
    let category: NotificationCategory?

    init(
        id: UUID = UUID(),
        title: String,
        body: String,
        timestamp: Date = Date(),
        isRead: Bool = false,
        stationId: String? = nil,
        category: NotificationCategory? = nil
    ) {
        self.id = id
        self.title = title
        self.body = body
        self.timestamp = timestamp
        self.isRead = isRead
        self.stationId = stationId
        self.category = category
    }
}

enum NotificationCategory: String, Codable {
    case atmospheric
    case light
    case soil
    case airQuality
    case precipitation
    case trailActivity
    case general
}
