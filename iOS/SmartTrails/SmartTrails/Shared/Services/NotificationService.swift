//
//  NotificationService.swift
//  SmartTrails
//
//  Created by Kate Dmitrieva on 28/11/25.
//

import Foundation
import UserNotifications
import Combine

#if os(iOS)
import UIKit
#endif

@MainActor
final class NotificationService: NSObject, ObservableObject {
    static let shared = NotificationService()

    // MARK: - Published Properties

    @Published private(set) var notifications: [NotificationItem] = []
    @Published private(set) var unreadCount: Int = 0
    @Published var shouldNavigateToNotifications: Bool = false

    // MARK: - Storage Keys

    private let notificationsStorageKey = "smarttrails_notifications"
    private let maxStoredNotifications = 50

    override init() {
        super.init()
        loadNotificationsFromStorage()
    }

    // MARK: - Authorization

   /// Request notification permissions
    func requestAuthorization() async -> Bool {
        let center = UNUserNotificationCenter.current()

        do {
           let granted = try await center.requestAuthorization(options: [.alert, .sound, .badge])

            if granted {
                registerForRemoteNotifications()
            }

           return granted
        } catch {
            print("Notification authorization error: \(error)")
            return false
        }
    }

    func checkAuthorizationStatus() async -> UNAuthorizationStatus {
        let settings = await UNUserNotificationCenter.current().notificationSettings()
        return settings.authorizationStatus
    }

   // MARK: - Remote Notifications

    private func registerForRemoteNotifications() {
        #if os(iOS)
       UIApplication.shared.registerForRemoteNotifications()
        #endif
    }

   /// Handle device token from APNs
    func handleDeviceToken(_ deviceToken: Data) {
        let token = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        print("📱 iOS Device Token: \(token)")

        NetworkService.shared.registerDeviceToken(
            token: token,
            platform: "ios",
            bundleId: "com.kateDmitrieva.SmartTrails"
        )
    }

    func handleRegistrationError(_ error: Error) {
        // no-op for now
    }

    // /// Send device token to backend for push notification targeting (old implementation)
    // func sendTokenToBackend(_ token: String) async throws {
    //     guard let url = URL(string: "https://smartTrails.com/api/devices/register") else {
    //         throw NetworkError.invalidURL
    //     }
    //
    //     var request = URLRequest(url: url)
    //     request.httpMethod = "POST"
    //     request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    //
    //     let body = ["device_token": token, "platform": "ios"]
    //     request.httpBody = try JSONEncoder().encode(body)
    //
    //     let (_, response) = try await URLSession.shared.data(for: request)
    //     guard let httpResponse = response as? HTTPURLResponse,
    //           (200...299).contains(httpResponse.statusCode) else {
    //         throw NetworkError.serverError(statusCode: (response as? HTTPURLResponse)?.statusCode ?? 500)
    //     }
    //
    //     print("sending token to backend", token)
    // }

    /// Send device token to backend for push notification targeting
    func sendTokenToBackend(_ token: String, platform: String = "ios", bundleId: String = "com.kateDmitrieva.SmartTrails") {
        NetworkService.shared.registerDeviceToken(
            token: token,
            platform: platform,
            bundleId: bundleId
        )
    }

    // MARK: - Notification Management

    /// Add a new notification to the list
    func addNotification(_ notification: NotificationItem) {
        // Insert at the beginning (newest first)
        notifications.insert(notification, at: 0)

        // Trim if exceeds max
        if notifications.count > maxStoredNotifications {
            notifications = Array(notifications.prefix(maxStoredNotifications))
        }

        updateUnreadCount()
        saveNotificationsToStorage()
    }

    /// Mark all notifications as read
    func markAllAsRead() {
        for index in notifications.indices {
            notifications[index].isRead = true
        }

        updateUnreadCount()
        saveNotificationsToStorage()
    }

    /// Clear all notifications
    func clearAllNotifications() {
        notifications.removeAll()
        updateUnreadCount()
        saveNotificationsToStorage()
    }

    /// Update the unread count
    private func updateUnreadCount() {
        unreadCount = notifications.filter { !$0.isRead }.count
    }

    // MARK: - Persistence

    private func saveNotificationsToStorage() {
        if let encoded = try? JSONEncoder().encode(notifications) {
            UserDefaults.standard.set(encoded, forKey: notificationsStorageKey)
        }
    }

    private func loadNotificationsFromStorage() {
        if let data = UserDefaults.standard.data(forKey: notificationsStorageKey),
           let decoded = try? JSONDecoder().decode([NotificationItem].self, from: data) {
            notifications = decoded
            updateUnreadCount()
        }
    }

    /// Parse category from notification payload
    private func parseCategory(from userInfo: [AnyHashable: Any]) -> NotificationCategory? {
        if let categoryString = userInfo["category"] as? String {
            return NotificationCategory(rawValue: categoryString)
        }
        return nil
    }
}

// MARK: - UNUserNotificationCenterDelegate

extension NotificationService: UNUserNotificationCenterDelegate {
    // app in foreground
    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        // Store the notification
        let content = notification.request.content
        let userInfo = content.userInfo

        let notificationItem = NotificationItem(
            title: content.title,
            body: content.body,
            timestamp: Date(),
            isRead: false,
            stationId: userInfo["station_id"] as? String,
            category: parseCategoryFromUserInfo(userInfo)
        )

        DispatchQueue.main.async {
            Task { @MainActor in
                self.addNotification(notificationItem)
            }
        }

        // Show banner and play sound even when app is in foreground
        completionHandler([.banner, .sound, .badge])
    }

    // user tapping
    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        let content = response.notification.request.content
        let userInfo = content.userInfo

        // Store the notification if not already stored (app was in background/terminated)
        let notificationItem = NotificationItem(
            title: content.title,
            body: content.body,
            timestamp: response.notification.date,
            isRead: false,
            stationId: userInfo["station_id"] as? String,
            category: parseCategoryFromUserInfo(userInfo)
        )

        if let stationId = userInfo["station_id"] as? String {
            print("📬 Notification tapped for station: \(stationId)")
        }

        DispatchQueue.main.async {
            Task { @MainActor in
                // Check if notification already exists (by comparing title, body, and approximate timestamp)
                let isDuplicate = self.notifications.contains { existing in
                    existing.title == notificationItem.title &&
                    existing.body == notificationItem.body &&
                    abs(existing.timestamp.timeIntervalSince(notificationItem.timestamp)) < 5
                }

                if !isDuplicate {
                    self.addNotification(notificationItem)
                }

                // Navigate to notifications view after a small delay to let app fully launch
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                    Task { @MainActor in
                        self.shouldNavigateToNotifications = true
                    }
                }
            }
        }

        completionHandler()
    }

    /// Parse category from notification payload (nonisolated for delegate use)
    nonisolated private func parseCategoryFromUserInfo(_ userInfo: [AnyHashable: Any]) -> NotificationCategory? {
        if let categoryString = userInfo["category"] as? String {
            return NotificationCategory(rawValue: categoryString)
        }
        return nil
    }
}
