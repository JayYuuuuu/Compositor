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
            let space = try XCTUnwrap(CGColorSpace(name: CGColorSpace.sRGB))
            let context = try XCTUnwrap(CGContext(data: nil, width: 16, height: 16, bitsPerComponent: 8,
                bytesPerRow: 64, space: space, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue))
            context.setFillColor(CGColor(srgbRed: 1, green: 0, blue: 0, alpha: 1))
            context.fill(CGRect(x: 0, y: 0, width: 16, height: 16))
            let bitmap = NSBitmapImageRep(cgImage: try XCTUnwrap(context.makeImage()))
            try XCTUnwrap(bitmap.representation(using: .png, properties: [:])).write(to: input)
            let fixture = try XCTUnwrap(NSBitmapImageRep(data: try Data(contentsOf: input)))
            let fixturePixel = try XCTUnwrap(fixture.colorAt(x: 8, y: 8)?.usingColorSpace(.sRGB))
            XCTAssertGreaterThan(fixturePixel.redComponent, 0.9)
            XCTAssertGreaterThan(fixturePixel.alphaComponent, 0.9)
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
            let pngWritten = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
                guard let data = try? Data(contentsOf: output) else { return false }
                return NSBitmapImageRep(data: data) != nil
            }, object: nil)
            XCTAssertEqual(XCTWaiter.wait(for: [pngWritten], timeout: 10), .completed)
            let exported = try XCTUnwrap(NSBitmapImageRep(data: try Data(contentsOf: output)))
            XCTAssertEqual(exported.pixelsWide, 64)
            XCTAssertEqual(exported.pixelsHigh, 32)
            let inputAttachment = XCTAttachment(contentsOfFile: input)
            inputAttachment.name = "Input fixture"; inputAttachment.lifetime = .keepAlways; add(inputAttachment)
            let outputAttachment = XCTAttachment(contentsOfFile: output)
            outputAttachment.name = "Exported pixels"; outputAttachment.lifetime = .keepAlways; add(outputAttachment)
            let center = try XCTUnwrap(exported.colorAt(x: 32, y: 16)?.usingColorSpace(.sRGB))
            XCTAssertGreaterThan(center.redComponent, 0.9)
            XCTAssertGreaterThan(center.alphaComponent, 0.9)

            app.typeKey("s", modifierFlags: .command)
            save(to: folder, name: "localized-project.comp", in: app)
            let project = folder.appendingPathComponent("localized-project.comp")
            let projectWritten = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
                FileManager.default.fileExists(atPath: project.appendingPathComponent("manifest.json").path)
            }, object: nil)
            XCTAssertEqual(XCTWaiter.wait(for: [projectWritten], timeout: 10), .completed)
            file.click()
            app.menuItems[label("Close Project", "关闭项目")].click()
            file.click()
            app.menuItems[label("Open Project…", "打开项目…")].click()
            choosePath(project.path, in: app)
            confirmFilePanel(in: app)
            expectation(for: imported, evaluatedWith: app.staticTexts["layerCount"])
            waitForExpectations(timeout: 10)
            XCTAssertEqual(app.staticTexts["canvasDimensions"].value as? String, "64 × 32 px")

            app.menuBars.menuBarItems[label("Filter", "滤镜")].click()
            app.menuItems[label("Camera Raw Filter…", "Camera Raw 滤镜…")].click()
            let rawSections = [("Light", "光线"), ("Color", "颜色"), ("Color Grading", "颜色分级"),
                ("Effects", "效果"), ("Curve", "曲线"), ("Color Mixer", "混色器"), ("Detail", "细节"),
                ("Optics", "光学"), ("Geometry", "几何"), ("Calibration", "校准")]
            for (english, translated) in rawSections {
                let section = app.buttons["rawSection-" + english]
                XCTAssertTrue(section.waitForExistence(timeout: 5))
                XCTAssertEqual(section.label, label(english, translated))
            }
            // Close initially open sections so the advanced controls remain within the viewport.
            for name in ["Light", "Color", "Color Grading"] { app.buttons["rawSection-" + name].click() }
            app.buttons["rawSection-Curve"].click()
            let point = app.radioButtons[label("Point", "点曲线")]
            XCTAssertTrue(point.waitForExistence(timeout: 5))
            point.click()
            XCTAssertTrue(app.radioButtons[label("Red", "红色")].waitForExistence(timeout: 5))
            let rawScreenshot = XCTAttachment(screenshot: app.screenshot())
            rawScreenshot.name = chinese ? "Chinese RAW point curve" : "English RAW point curve"
            rawScreenshot.lifetime = .keepAlways; add(rawScreenshot)
            app.buttons[label("Cancel", "取消")].click()

            app.menuBars.menuBarItems[label("Edit", "编辑")].click()
            app.menuItems[label("Keyboard Shortcuts…", "键盘快捷键…")].click()
            let shortcutSearch = app.textFields[label("Search shortcuts", "搜索快捷键")]
            XCTAssertTrue(shortcutSearch.waitForExistence(timeout: 5))
            shortcutSearch.typeText(label("Decrease brush size", "减小画笔大小"))
            XCTAssertTrue(app.staticTexts[label("Decrease brush size", "减小画笔大小")].waitForExistence(timeout: 5))
            app.buttons[label("Cancel", "取消")].click()
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
