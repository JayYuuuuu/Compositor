# 简体中文汉化维护

## 项目定位

- 社区公开分支：https://github.com/JayYuuuuu/Compositor
- 上游：https://github.com/robbietilton/Compositor
- 许可：沿用 MIT，保留原作者版权和许可证。明确社区分支身份，不宣称官方中文版。
- 用户决定（2026-10-10）：建立公开 fork，在 devbox 保留固定项目目录，后续持续维护汉化。
- 目标：基于源码增加简体中文界面，保留英文；先提供可构建的中文版，是否提供安装到既有应用中的独立语言补丁，需单独验证，当前不作承诺。
- 上游 README 当前明确不接受翻译 PR；不向上游提交汉化 PR。

## 当前状态

2026-10-10 完成首批源码汉化，集中维护 590 条英文/简体中文翻译。macOS 构建与中英文相关回归已通过；实际中文菜单已读回，但完整窗口交互、中文排版和正式沙箱运行尚未验收。没有发布或安装中文版。

初始上游基线：`b4bfdea87f9dc0cbc9eabfa63683eb1b9c2bca60`。这是初始化版本，不表示后续已同步最新上游；每次合并更新须记录新基线和验证结果。

## 已查到的源码事实

初始化基线的静态检查（用于说明首批修复，不代表当前实现）：

- 仓库树包含 234 个 Swift 文件，未包含 `.xcstrings`、`.strings` 或 `.lproj` 翻译资源。该结果仅说明资源现状，不等于已统计所有待翻译文字。
- `Compositor/CompositorApp.swift` 包含直接写在界面里的英文菜单和动态撤销/重做文字。
- `Compositor/UI/BlendModePicker.swift` 用 `mode.rawValue` 显示菜单，同时通过菜单标题构造 `LayerBlendMode`。汉化该控件时须先解耦显示名称与内部识别值。
- `Compositor/UI/CommandPalette.swift` 从菜单收集命令，且存在从标题生成 ID 的逻辑。须核对语言切换对搜索、去重、快捷键和命令身份的影响。
- `Config/Info.plist` 的 Sparkle 更新源和公钥属于上游；`scripts/publish.sh` 中发布目标也固定为上游仓库。

以上没有经过应用运行验证。不能把静态检查写成已验证的交互结论。

## 实现约束

优先复用 Apple 原生本地化机制，集中维护翻译资源，避免两套 UI。英文保留为回退语言，简体中文对应 `zh-Hans`。具体语言选择行为在首个实现提交中记录；新增应用内语言设置需先确认产品方向。

内部 ID、枚举原始值、序列化值、快捷键标识、项目格式和用户输入内容保持独立于界面语言。不直接全局替换源码中的英文。AppKit 控件用稳定的关联值识别选项，不解析翻译后的显示标题。

首批覆盖菜单、工具栏、图层面板、常用弹窗和导入/导出流程，本批也覆盖命令搜索、部分调整/滤镜名称、导入/导出错误和辅助功能标签；随后补齐调整/滤镜内部控件、快捷键设置和剩余操作提示。图像编辑术语保持统一，建立翻译术语表；占位符、插值和数量表达按完整句子处理。

## 跟进上游

本地 `origin` 指向社区 fork，`upstream` 指向原项目，均采用 SSH。

```sh
git fetch upstream
git log --oneline HEAD..upstream/main
git merge upstream/main
```

先确认工作区和当前分支，保留已有修改；共享分支仅追加提交，不强推。合并后检查新增 UI 文字及本地化冲突，按改动范围验证，再提交并推送到社区 fork。记录此次合并的上游 SHA、翻译范围和实际验证结果。

## 构建和验收

上游要求 Apple silicon、macOS 26+、Xcode 26+。devbox 是 Linux 开发容器，可以编辑与做静态检查，不能代替 macOS 构建和真实 UI 验收。构建机和签名资料的私有细节不写进公开仓库。

构建与单元测试命令见 [AGENTS.md](../AGENTS.md)。汉化交付还需实际验证：中英文菜单、混合模式的选择与效果、撤销/重做、命令搜索和快捷键、导入/导出、旧项目读写，以及中文文本布局。编译成功不代替这些交互验证。涉及文件兼容性的修改，使用旧版项目做往返验证；汉化本身不应需要改变项目格式。

文档初始化不需要应用全量测试；首次功能实现必须完成适用的构建与真实交互验证。性能涉及的改动按项目总规则实测，不给未经测量的耗时或收益结论。

## 发布前提

当前继承的发布脚本尚未适配本分支，不运行它们。首次分发前必须明确独立应用身份、安装共存行为、发布目标、签名与公证策略，以及 Sparkle 更新策略；这些属于发布方案，实施前向用户确认。

中文版不能沿用原版的更新源与签名公钥：需为本分支配置自己的更新链路，或明确禁用更新。发布脚本必须指向本 fork，并验证不会对上游创建 release 或推送更新信息。不得把上游已签名/已公证的说明用于尚未验证的社区构建。

密钥、证书、令牌、构建机地址、账号凭据、日志和构建产物中的私有路径不进入 Git。发布前核对本次提交与产物，并保留 MIT 许可及原作者声明。

## 维护记录

| 日期 | 上游基线 | 完成范围 | 实际验证 | 未完成 |
| --- | --- | --- | --- | --- |
| 2026-10-10 | `b4bfdea` | 公开 fork、本地目录、维护文档 | 远端身份及公开属性回读；文档链接和提交检查 | 汉化实现、macOS 构建、交互验收、安装包 |
| 2026-10-10 | `b4bfdea` | 首批源码汉化、590 条双语资源、模型/显示解耦、回归与维护工具 | macOS 构建；英文及中文相关回归通过；真实中文菜单回读；目录检查及命令微基准 | 正式沙箱运行、完整窗口交互/排版、真实历史文件、剩余文字；发布方案及安装包 |

## 首批实现（2026-10-10）

采用 Apple 原生 `Localizable.xcstrings`，源语言 `en`，新增 `zh-Hans`；SwiftUI 字面量使用原生本地化，动态显示值与 AppKit 控件通过 `L10n.text` 查询同一目录，含参数的句子使用原生插值或 `L10n.format`。未添加应用内语言设置：跟随 macOS 语言及系统“应用程序语言”设置，更改后重新启动应用。未知键回退到原英文。目录维护参考 [Apple 字符串目录文档](https://developer.apple.com/documentation/Xcode/localizing-and-varying-text-with-a-string-catalog)。

所有维护的键同时保留英文和中文。目录关闭自动 Swift 符号生成，因为英文菜单省略号、大小写不同的键会生成重名符号；本分支不使用这些生成符号。动态键手动登记，新增界面文字需检查调用点和目录，不能把编译器提取到文字等同于运行时会翻译。

首批范围：菜单及动态菜单、工具名称/工具栏常用参数、图层面板和右键菜单、26 个混合模式、新画布/画布大小/图像大小/修边/拾色器、PSD 转换确认、导入状态及常见错误、导出预览及存储确认。尚未全量翻译所有调整和滤镜内部控件、RAW 开发控件、快捷键设置、更新对话框、状态栏长操作提示和 PSD 转换的逐条技术说明。图层名、项目名、字体名和其他用户内容不翻译；默认生成的图层名仍是英文，避免对已有命名/查重逻辑造成连带变化。

混合模式菜单将未改动的原始值放在 `representedObject` 中；高亮预览、选择和同步均读取关联值，不再解析菜单标题。图层“添加蒙版”菜单校验使用固定菜单标识。命令搜索按当前菜单显示语言匹配，支持中文字符；本批不提供拼音或跨语言别名搜索。菜单命令 ID 使用菜单结构位置，工具及蒙版命令使用固定未翻译的键；菜单 ID 只用于当次列表，不作为持久标识。执行前检查位置、可用性、动作、快捷键和当前标题，结构变动时拒绝误执行。系统菜单及搜索自身在中英文都排除。撤销/重做完整句子及调整、图层效果动作名独立翻译；历史不写入项目文件。

快捷键定义的英文标题仍是固定内部键的一部分，显示翻译不能改变它；本批没有修改快捷键定义、存储键或按键分派。项目格式版本、枚举原始值、图层数据和文件扩展名未改变。更新源、公钥、应用身份和发布脚本未修改。

### 翻译术语

| 英文 | 简体中文 |
| --- | --- |
| Canvas / Layer / Adjustment Layer | 画布 / 图层 / 调整图层 |
| Selection / Marquee / Lasso | 选区 / 选框 / 套索 |
| Layer Mask / Clipping Mask | 图层蒙版 / 剪贴蒙版 |
| Blend Mode / Opacity | 混合模式 / 不透明度 |
| Normal / Multiply / Screen / Overlay | 正常 / 正片叠底 / 滤色 / 叠加 |
| Hue / Saturation / Luminosity | 色相 / 饱和度 / 明度 |
| Curves / Levels / Color Balance | 曲线 / 色阶 / 色彩平衡 |
| Feather / Transform / Trim | 羽化 / 变换 / 修边 |
| Undo / Redo / Export As | 撤销 / 重做 / 导出为 |
| Save / Save As / Don’t Save | 存储 / 另存为 / 不存储 |

### 实际验证及边界

实机环境：Apple silicon，macOS 27.0.1、Xcode 27.0（27A266a）。首次默认构建遇到目录符号重名及控件 API 问题，修复后标准 `build` 已通过。临时开发验证使用 ad-hoc 签名，不是分发签名，不构建安装包。

测试宿主在沙箱初始化处等待，进程采样实际停在 `_libsecinit_appsandbox` 的 XPC 请求。仅对临时验证命令覆盖 `ENABLE_APP_SANDBOX=NO CODE_SIGN_ENTITLEMENTS=`，源码中的正式沙箱配置未变。因此下面的运行测试不能代表正式沙箱行为已验收。

英文环境相关回归：51 项测试、55 次运行（含参数化），0 失败；覆盖原生菜单命令执行和快捷键、撤销/重做、图层混合及像素结果、项目存储重开、导入、PNG/JPEG/PDF 导出、新画布及新增本地化测试。中文环境相关回归：33 项测试、37 次运行（含参数化），0 失败；最后补齐 PSD 标题和辅助功能文字后，再跑本地化、图像导入与 PSB 三组，共 15 项测试、19 次运行，0 失败；覆盖本地化、图层混合、项目读写、图像导入及导出。新增本地化测试直接创建实际 AppKit 混合模式控件，把显示标题改为“正片叠底”，验证预览、提交、撤销及重做仍使用 `.multiply`；同时检查英文/中文资源、缺键回退、含 `%@` 的用户文件名原样保留、枚举仍编码英文原始值、重复菜单标题的独立 ID、中文命令搜索及禁用命令拒绝执行。

通过系统辅助功能接口读回真实中文菜单，包括“新建画布…”“导入图像…”“导出为…”；这只验证菜单文字。新建独立 `CompositorLocalization` scheme 和双语核心流程 UI 测试，首次执行被测试运行器拒绝，错误为 `System authentication is running` / `LocalAuthentication Code=-4`。没有改系统认证设置，未把失败的自动界面测试当成功。仍需在可操作的桌面会话完成中英文窗口交互、中文文字布局、真实文件选择及导出落盘验收。已有项目测试验证的是程序生成项目的往返读写；尚未使用一份由汉化前应用实际生成的历史项目做人工验收。

目录静态验证通过：590 条双语资源，占位符类型及位置一致；检查器内含正反例，避免空检查误报通过。编译后两种语言资源合计 153,688 字节（初始化版本无翻译资源）。命令列表微基准：同一台 Mac、优化编译、300 条命令，每组 50 次收集及搜索，7 组取中位数；初始化版本 0.915 ms/次，本批 0.804 ms/次，每版均匹配 105,000 条结果。这个基准不包含整个应用启动、绘图、窗口布局或真实键盘输入耗时，不能据此推断整体更快。

### 复现入口

Linux 静态检查：

```sh
python3 scripts/validate-localization.py
git diff --check
```

macOS 编译：

```sh
xcodebuild -project Compositor.xcodeproj -scheme Compositor \
  -destination 'platform=macOS' -packageAuthorizationProvider netrc \
  CODE_SIGNING_ALLOWED=NO build
```

英文相关回归（临时关闭沙箱只用于复现本次开发验证）：

```sh
xcodebuild -project Compositor.xcodeproj -scheme Compositor \
  -destination 'platform=macOS' -packageAuthorizationProvider netrc \
  CODE_SIGN_IDENTITY=- DEVELOPMENT_TEAM= ENABLE_APP_SANDBOX=NO CODE_SIGN_ENTITLEMENTS= \
  test -testLanguage en -testRegion US \
  -only-testing:CompositorTests/LocalizationTests \
  -only-testing:CompositorTests/CommandPaletteTests \
  -only-testing:CompositorTests/BlendShortcutTests \
  -only-testing:CompositorTests/LayerAppearanceTests \
  -only-testing:CompositorTests/HistoryTests \
  -only-testing:CompositorTests/ProjectTests \
  -only-testing:CompositorTests/ExportTests \
  -only-testing:CompositorTests/JPEGExportTests \
  -only-testing:CompositorTests/ImageImportTests \
  -only-testing:CompositorTests/CanvasEntryTests
```

中文回归改为 `-testLanguage zh-Hans -testRegion CN`，只选上述本地化、图层外观、项目、导出、JPEG 导出、图像导入六组测试（其余旧测试有英文显示文字假设）。UI 测试用 `CompositorLocalization` scheme，指定 `-only-testing:CompositorUITests/LocalizationUITests`，目前等待桌面认证障碍解除后验收；这不会在常规 unit-test scheme 中自动运行。命令微基准用 `python3 scripts/benchmark-command-palette.py --baseline 9a319ff`，必须在 macOS 执行。

本次实际 fetch 后，上游仍为 `b4bfdea87f9dc0cbc9eabfa63683eb1b9c2bca60`，没有需要合并的新提交。维护期间工作区初始干净，没有覆盖他人修改。
