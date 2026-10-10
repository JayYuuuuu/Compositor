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
