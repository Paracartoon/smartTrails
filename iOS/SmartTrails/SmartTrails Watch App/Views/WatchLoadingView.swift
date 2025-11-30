//
//  WatchLoadingView.swift
//  SmartTrails Watch App
//
//  Created by Kate Dmitrieva on 30/11/25.
//

import SwiftUI

struct WatchLoadingView: View {
    @State private var isAnimating = false

    var body: some View {
        ZStack {
            WatchTheme.appBackground
                .ignoresSafeArea()

          VStack(spacing: 12) {
                Image(systemName: "mountain.2.fill")
                    .font(.system(size: 40))
//                    .foregroundStyle(
//                      LinearGradient(
//                            colors: [WatchTheme.atmosphericColor, .white],
//                            startPoint: .top,
//                            endPoint: .bottom
//                        )
//                    )
                    .scaleEffect(isAnimating ? 1.05 : 1.0)
                    .animation(
                        .easeInOut(duration: 1.0).repeatForever(autoreverses: true),
                        value: isAnimating
                    )

                Text("SmartTrails")
                    .font(.headline)
                    .fontWeight(.bold)
                    .foregroundColor(.white)

                // loading indicator
                ProgressView()
                    .tint(.cyan)
            }
        }
        .onAppear {
          isAnimating = true
        }
    }
}


