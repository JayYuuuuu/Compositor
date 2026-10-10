import AppKit
import XCTest

final class LocalizationUITests: XCTestCase {
    override func setUpWithError() throws { continueAfterFailure = false }

    @MainActor
    func testChineseAndEnglishCoreWorkflow() throws {
        for chinese in [true, false] {
            let app = XCUIApplication()
            app.launchArguments = ["-AppleLanguages", chinese ? "(zh-Hans)" : "(en)",
                                   "-AppleLocale", chinese ? "zh_CN" : "en_US",
                                   "-SUEnableAutomaticChecks", "NO", "-SUHasLaunchedBefore", "YES",
                                   "-ApplePersistenceIgnoreState", "YES"]
            app.launch()
            defer { app.terminate() }
            func label(_ english: String, _ translated: String) -> String { chinese ? translated : english }
            let file = app.menuBars.menuBarItems[label("File", "文件")]
            XCTAssertTrue(file.waitForExistence(timeout: 10))
            file.click()
            app.menuItems[label("New Canvas…", "新建画布…")].click()
            let create = app.buttons["createCanvas"]
            XCTAssertTrue(create.waitForExistence(timeout: 5))
            let width = app.textFields["widthInput"], height = app.textFields["heightInput"]
            width.click(); width.typeKey("a", modifierFlags: .command); width.typeText("64")
            height.click(); height.typeKey("a", modifierFlags: .command); height.typeText("32")
            create.click()
            let dimensions = app.staticTexts["canvasDimensions"]
            XCTAssertTrue(dimensions.waitForExistence(timeout: 5))
            XCTAssertEqual(dimensions.value as? String, "64 × 32 px")
            let blend = app.popUpButtons[label("Blend mode", "混合模式")]
            XCTAssertTrue(blend.waitForExistence(timeout: 5))
            blend.click()
            app.menuItems[label("Multiply", "正片叠底")].click()
            XCTAssertEqual(blend.value as? String, label("Multiply", "正片叠底"))
            app.menuBars.menuBarItems[label("Edit", "编辑")].click()
            let undo = app.menuItems[label("Undo Layer Blend Mode", "撤销图层混合模式")]
            XCTAssertTrue(undo.exists)
            undo.click()
            XCTAssertEqual(blend.value as? String, label("Normal", "正常"))
            app.typeKey("z", modifierFlags: [.command, .shift])
            XCTAssertEqual(blend.value as? String, label("Multiply", "正片叠底"))
            app.typeKey("f", modifierFlags: .command)
            let search = app.textFields[label("Search commands and tools", "搜索命令和工具")]
            XCTAssertTrue(search.waitForExistence(timeout: 5))
            search.typeText(label("Gaussian Blur", "高斯模糊"))
            XCTAssertTrue(app.staticTexts[label("Filter › Gaussian Blur…", "滤镜 › 高斯模糊…")].waitForExistence(timeout: 5))
            app.typeKey(.escape, modifierFlags: [])
            file.click()
            app.menuItems[label("Export As…", "导出为…")].click()
            XCTAssertTrue(app.buttons[label("Export…", "导出…")].waitForExistence(timeout: 5))
            let screenshot = XCTAttachment(screenshot: app.screenshot())
            screenshot.name = chinese ? "Simplified Chinese export" : "English export"
            screenshot.lifetime = .keepAlways
            add(screenshot)
            app.buttons[label("Cancel", "取消")].click()

            let folder = FileManager.default.temporaryDirectory.appendingPathComponent("CompositorLocalization-" + UUID().uuidString)
            try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: false)
            defer { try? FileManager.default.removeItem(at: folder) }
            let input = folder.appendingPathComponent("localized-input.png")
            let bitmap = try XCTUnwrap(NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 16, pixelsHigh: 16,
                bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
                colorSpaceName: .deviceRGB, bytesPerRow: 64, bitsPerPixel: 32))
            for y in 0..<16 { for x in 0..<16 { bitmap.setColor(NSColor(red: 1, green: 0, blue: 0, alpha: 1), atX: x, y: y) } }
            try XCTUnwrap(bitmap.representation(using: .png, properties: [:])).write(to: input)
            file.click()
            app.menuItems[label("Import Images…", "导入图像…")].click()
            choosePath(input.path, in: app)
            confirmFilePanel(in: app)
            let count = app.staticTexts["layerCount"]
            let imported = NSPredicate(format: "value == %@", "2")
            expectation(for: imported, evaluatedWith: count)
            waitForExpectations(timeout: 10)

            file.click()
            app.menuItems[label("Export PNG…", "导出 PNG…")].click()
            save(to: folder, name: "localized-output.png", in: app)
            let output = folder.appendingPathComponent("localized-output.png")
            XCTAssertTrue(FileManager.default.fileExists(atPath: output.path))
            let exported = try XCTUnwrap(NSBitmapImageRep(data: try Data(contentsOf: output)))
            XCTAssertEqual(exported.pixelsWide, 64)
            XCTAssertEqual(exported.pixelsHigh, 32)
            let center = try XCTUnwrap(exported.colorAt(x: 32, y: 16)?.usingColorSpace(.sRGB))
            XCTAssertGreaterThan(center.redComponent, 0.9)
            XCTAssertGreaterThan(center.alphaComponent, 0.9)

            app.typeKey("s", modifierFlags: .command)
            save(to: folder, name: "localized-project.comp", in: app)
            let project = folder.appendingPathComponent("localized-project.comp")
            XCTAssertTrue(FileManager.default.fileExists(atPath: project.appendingPathComponent("manifest.json").path))
            file.click()
            app.menuItems[label("Close Project", "关闭项目")].click()
            file.click()
            app.menuItems[label("Open Project…", "打开项目…")].click()
            choosePath(project.path, in: app)
            confirmFilePanel(in: app)
            expectation(for: imported, evaluatedWith: app.staticTexts["layerCount"])
            waitForExpectations(timeout: 10)
            XCTAssertEqual(app.staticTexts["canvasDimensions"].value as? String, "64 × 32 px")
        }
    }

    @MainActor
    private func choosePath(_ path: String, in app: XCUIApplication) {
        app.typeKey("g", modifierFlags: [.command, .shift])
        app.typeText(path)
        app.typeKey(.return, modifierFlags: [])
    }

    @MainActor
    private func confirmFilePanel(in app: XCUIApplication) {
        // Native file-panel buttons expose a title, not a SwiftUI label; their stable ID holds in either language.
        let button = app.buttons["OKButton"]
        XCTAssertTrue(button.waitForExistence(timeout: 5))
        button.click()
    }

    @MainActor
    private func save(to folder: URL, name: String, in app: XCUIApplication) {
        choosePath(folder.path, in: app)
        let field = app.textFields["saveAsNameTextField"]
        XCTAssertTrue(field.waitForExistence(timeout: 5))
        field.click()
        field.typeKey("a", modifierFlags: .command)
        field.typeText(name)
        confirmFilePanel(in: app)
    }
}
