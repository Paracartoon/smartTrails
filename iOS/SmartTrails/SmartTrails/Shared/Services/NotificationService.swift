//
//  NotificationService.swift
//  SmartTrails
//
//  Created by Kate Dmitrieva on 28/11/25.
//

import Foundation
import UserNotifications

#if os(iOS)
import UIKit
#endif

final class NotificationService: NSObject {
   static let shared = NotificationService()

    private override init() {
        super.init()
    }

    // MARK: - Authorization

   /// Request notification permissions
    func requestAuthorization() async -> Bool {
        let center = UNUserNotificationCenter.current()

        do {
           let granted = try await center.requestAuthorization(options: [.alert, .sound, .badge])

            if granted {
                await registerForRemoteNotifications()
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

    @MainActor
    private func registerForRemoteNotifications() {
        #if os(iOS)
       UIApplication.shared.registerForRemoteNotifications()
        #endif
    }

   /// Handle device token from APNs
    func handleDeviceToken(_ deviceToken: Data) {
        let token = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        print("11111 apns token token: ", token)

       // for thr backend
        // Example:
        // Task {
        //     try await sendTokenToBackend(token)
        // }
    }

    func handleRegistrationError(_ error: Error) {
        print("111111 failed to register push notifications", error.localizedDescription)
    }

   /// Send device token to backend for push notification targeting
    func sendTokenToBackend(_ token: String) async throws {
        // guard let url = URL(string: "https://smartTrails.com/api/devices/register") else {
       //     throw NetworkError.invalidURL
        // }
        //
        // var request = URLRequest(url: url)
        // request.httpMethod = "POST"
        // request.setValue("application/json", forHTTPHeaderField: "Content-Type")
       //
        // let body = ["device_token": token, "platform": "ios"]
        // request.httpBody = try JSONEncoder().encode(body)
        //
        // let (_, response) = try await URLSession.shared.data(for: request)
        // guard let httpResponse = response as? HTTPURLResponse,
       //       (200...299).contains(httpResponse.statusCode) else {
        //     throw NetworkError.serverError(statusCode: (response as? HTTPURLResponse)?.statusCode ?? 500)
        // }

        print("11111111  sending token to backend", token)
    }
}

// MARK: - UNUserNotificationCenterDelegate

extension NotificationService: UNUserNotificationCenterDelegate {
   // app in foreground
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification
    ) async -> UNNotificationPresentationOptions {
        // Show banner and play sound even when app is in foreground
        return [.banner, .sound, .badge]
    }

   // user tapping
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse
    ) async {
        let userInfo = response.notification.request.content.userInfo

        // payload
       if let stationId = userInfo["station_id"] as? String {
            print("tapped for station with id: \(stationId)")
            // only one station in POC
            // no-op!
        }
    }
}
