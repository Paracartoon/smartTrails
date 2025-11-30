//
//  LoadingView.swift
//  SmartTrails
//
//  Created by Kate Dmitrieva on 30/11/25.
//

import SwiftUI

struct LoadingView: View {
   @State private var isAnimating = false


    var body: some View {
        VStack(spacing: 24) {

            Image(systemName: "mountain.2.fill")
                .font(.system(size: 80))
//                .foregroundStyle(
//                    LinearGradient(
//                        colors: [Theme.primary, Theme.slateGray],
//                       startPoint: .top,
//                        endPoint: .bottom
//                    )
//                )
                //.scaleEffect(isAnimating ? 0.5 : 2.0)
                .scaleEffect(isAnimating ? 1.05 : 1.0)
                .animation(
                    .easeInOut(duration: 1.0).repeatForever(autoreverses: true),
                    value: isAnimating
                )

           // app name label
            Text("SmartTrails")
                .font(.largeTitle)
                .fontWeight(.bold)
                .foregroundColor(Theme.textPrimary)

            // loading indicator
            ProgressView()
               .scaleEffect(1.5)
               //.padding(.horizontal)
                .tint(Theme.primary)

            // loading text
            Text("Loading trail data...")
                .font(.subheadline)
                .foregroundColor(Theme.textSecondary)
        }
       .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Theme.appBackground)
        .onAppear {
            isAnimating = true
        }
    }
}

