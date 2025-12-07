//
//  NotificationsView.swift
//  SmartTrails
//
//  Created by Kate Dmitrieva on 07/12/25.
//

import SwiftUI

struct NotificationsView: View {
    @ObservedObject var notificationService = NotificationService.shared
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ZStack {
            Theme.appBackground
                .ignoresSafeArea()

            if notificationService.notifications.isEmpty {
                emptyStateView
            } else {
                notificationsList
            }
        }
        .navigationTitle("Notifications")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                if !notificationService.notifications.isEmpty {
                    Button("Clear All") {
                        notificationService.clearAllNotifications()
                    }
                    .foregroundColor(Theme.danger)
                }
            }
        }
        .onAppear {
            notificationService.markAllAsRead()
        }
    }

    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "bell.slash")
                .font(.system(size: 50))
                .foregroundColor(Theme.textSecondary)

            Text("No Notifications")
                .font(.headline)
                .foregroundColor(Theme.textPrimary)

            Text("You'll see alerts about trail conditions here")
                .font(.subheadline)
                .foregroundColor(Theme.textSecondary)
                .multilineTextAlignment(.center)
        }
        .padding()
    }

    private var notificationsList: some View {
        ScrollView {
            LazyVStack(spacing: 12) {
                ForEach(notificationService.notifications) { notification in
                    NotificationRow(notification: notification)
                }
            }
            .padding()
        }
    }
}

struct NotificationRow: View {
    let notification: NotificationItem

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            // Category icon
            ZStack {
                Circle()
                    .fill(categoryColor.opacity(0.2))
                    .frame(width: 40, height: 40)

                Image(systemName: categoryIcon)
                    .font(.system(size: 18))
                    .foregroundColor(categoryColor)
            }

            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(notification.title)
                        .font(.headline)
                        .foregroundColor(Theme.textPrimary)

                    Spacer()

                    if !notification.isRead {
                        Circle()
                            .fill(Theme.danger)
                            .frame(width: 8, height: 8)
                    }
                }

                Text(notification.body)
                    .font(.subheadline)
                    .foregroundColor(Theme.textSecondary)
                    .lineLimit(2)

                Text(formattedTime)
                    .font(.caption)
                    .foregroundColor(Theme.textSecondary.opacity(0.7))
            }
        }
        .padding()
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.05), radius: 2, x: 0, y: 1)
    }

    private var categoryColor: Color {
        guard let category = notification.category else {
            return Theme.primary
        }

        switch category {
        case .atmospheric:
            return Theme.atmosphericColor
        case .light:
            return Theme.lightColor
        case .soil:
            return Theme.soilColor
        case .airQuality:
            return Theme.airQualityColor
        case .precipitation:
            return Theme.precipitationColor
        case .trailActivity:
            return Theme.trailActivityColor
        case .general:
            return Theme.primary
        }
    }

    private var categoryIcon: String {
        guard let category = notification.category else {
            return "bell.fill"
        }

        switch category {
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
        case .general:
            return "bell.fill"
        }
    }

    private var formattedTime: String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: notification.timestamp, relativeTo: Date())
    }
}
