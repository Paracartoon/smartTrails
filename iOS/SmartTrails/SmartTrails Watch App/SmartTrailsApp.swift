//
//  SmartTrailsApp.swift
//  SmartTrails Watch App
//
//  Created by Kate Dmitrieva on 30/11/25.
//

import SwiftUI

@main
struct SmartTrails_Watch_AppApp: App {
   @StateObject private var viewModel = WatchDashboardViewModel()


    var body: some Scene {
        WindowGroup {
          Group {
                if viewModel.isLoading {
                    // white?
                   WatchLoadingView()
                        .task {
                            await viewModel.loadInitialData()
                        }
                } else {
                    WatchDashboardView()
                      .environmentObject(viewModel)
                }
            }
        }
    }
}
