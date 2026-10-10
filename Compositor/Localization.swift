import Foundation

/// Native bundle lookup for display values that are not SwiftUI string literals.
/// Keys are English source text; model values and user content never pass through this helper.
nonisolated enum L10n {
    static func text(_ key: String, bundle: Bundle = .main) -> String {
        bundle.localizedString(forKey: key, value: key, table: "Localizable")
    }

    static func format(_ key: String, _ arguments: CVarArg...) -> String {
        String(format: text(key), locale: Locale.current, arguments: arguments)
    }
}

// Display names are separate from persisted RAW enum values.
extension CameraRawUprightMode {
    var displayName: String {
        switch self {
        case .off: String(localized: "Off")
        case .guided: String(localized: "Guided")
        }
    }
}
extension CameraRawProjection {
    var displayName: String {
        switch self {
        case .perspective: String(localized: "Perspective")
        case .rectilinear: String(localized: "Rectilinear")
        }
    }
}
extension CameraRawProcessVersion {
    var displayName: String {
        switch self {
        case .version1: String(localized: "Version 1")
        case .version2: String(localized: "Version 2")
        case .version3: String(localized: "Version 3")
        case .version4: String(localized: "Version 4")
        case .version5: String(localized: "Version 5")
        case .version6: String(localized: "Version 6")
        }
    }
}
extension CameraRawCurvePage {
    var displayName: String {
        switch self {
        case .parametric: String(localized: "Parametric")
        case .point: String(localized: "Point")
        }
    }
}
extension CameraRawPointChannel {
    var displayName: String {
        switch self {
        case .rgb: String(localized: "RGB")
        case .red: String(localized: "Red")
        case .green: String(localized: "Green")
        case .blue: String(localized: "Blue")
        }
    }
}
extension CameraRawMixerPage {
    var displayName: String {
        switch self {
        case .hsl: String(localized: "HSL")
        case .color: String(localized: "Color")
        case .point: String(localized: "Point Color")
        }
    }
}
extension CameraRawMixerTab {
    var displayName: String {
        switch self {
        case .hue: String(localized: "Hue")
        case .saturation: String(localized: "Saturation")
        case .luminance: String(localized: "Luminance")
        }
    }
}
extension CameraRawGradePage {
    var displayName: String {
        switch self {
        case .threeWay: String(localized: "Three-Way")
        case .shadows: String(localized: "Shadows")
        case .midtones: String(localized: "Midtones")
        case .highlights: String(localized: "Highlights")
        case .global: String(localized: "Global")
        }
    }
}
extension CameraRawWhiteBalance {
    var displayName: String {
        switch self {
        case .custom: String(localized: "Custom")
        case .auto: String(localized: "Auto")
        }
    }
}
extension CameraRawGlowStyle {
    var displayName: String {
        switch self {
        case .diffusion: String(localized: "Diffusion")
        case .bloom: String(localized: "Bloom")
        case .halation: String(localized: "Halation")
        }
    }
}
extension CameraRawVignetteStyle {
    var displayName: String {
        switch self {
        case .highlightPriority: String(localized: "Highlight Priority")
        case .colorPriority: String(localized: "Color Priority")
        case .paintOverlay: String(localized: "Paint Overlay")
        }
    }
}
extension CameraRawScopeMode {
    var displayName: String {
        switch self {
        case .histogram: String(localized: "Histogram")
        case .vectorscope: String(localized: "Vectorscope")
        }
    }
}
