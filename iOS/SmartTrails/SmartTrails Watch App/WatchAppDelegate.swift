//
//  WatchAppDelegate.swift
//  SmartTrails Watch App
//
//  Created by Kate Dmitrieva on 07/12/25.
//

import WatchKit
import UserNotifications

class WatchAppDelegate: NSObject, WKApplicationDelegate {

    func applicationDidFinishLaunching() {
        UNUserNotificationCenter.current().delegate = self
    }

    func didRegisterForRemoteNotifications(withDeviceToken deviceToken: Data) {
        let token = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        print("⌚ Watch Device Token: \(token)")

        NetworkService.shared.registerDeviceToken(
            token: token,
            platform: "watchos",
            bundleId: "com.kateDmitrieva.SmartTrails.watchkitapp"
        )
    }

    func didFailToRegisterForRemoteNotificationsWithError(_ error: Error) {
        print("11111 -->>>>  Watch failed to register for remote notifications: \(error)")
    }
}

// MARK: - UNUserNotificationCenterDelegate

extension WatchAppDelegate: UNUserNotificationCenterDelegate {

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification
    ) async -> UNNotificationPresentationOptions {
        return [.banner, .sound]
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse
    ) async {
        print("📬 Watch notification tapped")
    }
}
