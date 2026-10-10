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
                                   "-SUEnableAutomaticChecks", "NO", "-SUHasLaunchedBefore", "YES"]
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
        }
    }
}
