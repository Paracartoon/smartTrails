//
//  SmartTrailsApp.swift
//  SmartTrails Watch App
//
//  Created by Kate Dmitrieva on 30/11/25.
//

import SwiftUI
import UserNotifications

@main
struct SmartTrails_Watch_AppApp: App {
    @WKApplicationDelegateAdaptor(WatchAppDelegate.self) var appDelegate
    @StateObject private var viewModel = WatchDashboardViewModel()

    var body: some Scene {
        WindowGroup {
            Group {
                if viewModel.isLoading {
                    WatchLoadingView()
                        .task {
                            await viewModel.loadInitialData()
                            requestNotificationPermission()
                        }
                } else {
                    WatchDashboardView()
                        .environmentObject(viewModel)
                }
            }
        }
    }

    func requestNotificationPermission() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { granted, error in
            if granted {
                DispatchQueue.main.async {
                    WKApplication.shared().registerForRemoteNotifications()
                }
            } else if let error = error {
                print("❌ Watch notification permission denied: \(error)")
            }
        }
    }
}
