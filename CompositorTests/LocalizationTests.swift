import AppKit
import SwiftUI
import Testing
@testable import Compositor

@MainActor
struct LocalizationTests {
    @Test func nativeResourcesKeepEnglishAndChineseAndFallback() throws {
        func language(_ name: String) throws -> Bundle {
            let path = try #require(Bundle.main.path(forResource: name, ofType: "lproj"))
            return try #require(Bundle(path: path))
        }
        let english = try language("en"), chinese = try language("zh-Hans")
        #expect(L10n.text("Multiply", bundle: english) == "Multiply")
        #expect(L10n.text("Multiply", bundle: chinese) == "正片叠底")
        #expect(L10n.text("Undo %@", bundle: chinese) == "撤销%@")
        #expect(L10n.text("Untranslated future command", bundle: chinese) == "Untranslated future command")
        let file = "客户的图像 %@.comp"
        let message = String(format: L10n.text("Save changes to %@?", bundle: chinese), file)
        #expect(message == "要存储对“客户的图像 %@.comp”的更改吗？")
        #expect(LayerBlendMode(rawValue: "正片叠底") == nil)
        #expect(String(data: try JSONEncoder().encode(LayerBlendMode.multiply), encoding: .utf8) == "\"Multiply\"")
    }

    @Test func translatedBlendPickerPreviewsCommitsAndUndoesModelValue() throws {
        let session = EditorSession()
        session.createDocument(width: 16, height: 16, emptyLayer: true)
        let host = NSHostingView(rootView: BlendModePicker(session: session))
        host.frame = CGRect(x: 0, y: 0, width: 220, height: 30)
        host.layoutSubtreeIfNeeded()
        func find(_ view: NSView) -> NSPopUpButton? {
            if let button = view as? NSPopUpButton { return button }
            return view.subviews.lazy.compactMap(find).first
        }
        let button = try #require(find(host))
        let coordinator = try #require(button.target as? BlendModePicker.Coordinator)
        let menu = try #require(button.menu)
        let item = try #require(button.itemArray.first { ($0.representedObject as? String) == "Multiply" })
        item.title = "正片叠底" // Proves the callback cannot depend on the displayed title, in either app language.
        coordinator.menuWillOpen(menu)
        coordinator.menu(menu, willHighlight: item)
        #expect(session.displayedBlendMode(for: try #require(session.activeLayer)) == .multiply)
        #expect(session.activeLayer?.blendMode == .normal)
        button.select(item)
        coordinator.choose(button)
        #expect(session.activeLayer?.blendMode == .multiply)
        session.undo()
        #expect(session.activeLayer?.blendMode == .normal)
        session.redo()
        #expect(session.activeLayer?.blendMode == .multiply)
        coordinator.menuDidClose(menu)
    }

    @Test func paletteIdentityAndChineseSearchDoNotParseMenuTitles() throws {
        let root = NSMenu()
        let app = NSMenuItem(title: "Compositor", action: nil, keyEquivalent: "")
        app.submenu = NSMenu()
        root.addItem(app)
        let layer = NSMenuItem(title: "Layer", action: nil, keyEquivalent: "")
        let menu = NSMenu()
        layer.submenu = menu
        root.addItem(layer)
        let target = ActionTarget()
        for _ in 0..<2 {
            let item = NSMenuItem(title: "Duplicate Layer", action: #selector(ActionTarget.run(_:)), keyEquivalent: "j")
            item.target = target
            menu.addItem(item)
        }
        let english = CommandPaletteMenu.entries(in: root, skipping: [])
        layer.title = "图层"
        for item in menu.items { item.title = "复制图层" }
        let chinese = CommandPaletteMenu.entries(in: root, skipping: [])
        #expect(english.map(\.id) == chinese.map(\.id))
        #expect(Set(chinese.map(\.id)).count == 2)
        let matches = CommandPaletteSearch.rank(chinese, query: "复制")
        #expect(matches.count == 2)
        matches[1].perform()
        #expect(target.invocations == 1)
        menu.items[1].isEnabled = false
        matches[1].perform()
        #expect(target.invocations == 1)
        #expect(CommandPaletteSearch.score("图层", in: "图层 › 复制图层") != nil)
    }

    private final class ActionTarget: NSObject {
        var invocations = 0
        @objc func run(_ sender: Any?) { invocations += 1 }
    }
}
