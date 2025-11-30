//
//  SmartTrailsApp.swift
//  SmartTrails

import SwiftUI
import UserNotifications

// MARK: - App Delegate for Push Notifications

class AppDelegate: NSObject, UIApplicationDelegate {
   func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        // Set notification delegate!
        UNUserNotificationCenter.current().delegate = NotificationService.shared
        return true
    }

   func application(
        _ application: UIApplication,
        didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data
    ) {
        NotificationService.shared.handleDeviceToken(deviceToken)
    }

   func application(
        _ application: UIApplication,
        didFailToRegisterForRemoteNotificationsWithError error: Error
    ) {
        NotificationService.shared.handleRegistrationError(error)
    }
}

// MARK: - Main

@main
struct SmartTrailsApp: App {
   @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @StateObject private var viewModel = DashboardViewModel()

    // main app body
    var body: some Scene {
       WindowGroup {
            Group {
                if viewModel.isLoading {
                    LoadingView()
                       .task {
                            await viewModel.loadInitialData()
                            // Request notification permission after initial load
                           // 
                            _ = await NotificationService.shared.requestAuthorization()
                        }
               } else {
                    DashboardView()
                        .environmentObject(viewModel)
                }
            }
        }
    }
}
