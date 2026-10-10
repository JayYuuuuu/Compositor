#!/usr/bin/env python3
"""Opt-in macOS microbenchmark for menu collection + search; not an app launch benchmark."""
import argparse
from pathlib import Path
import platform
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = r"""
struct ShortcutChord { init(_ key: String, _ bits: Int) {} ; var label: String { "" } }
final class Target: NSObject { @objc func run(_ sender: Any?) {} }
let root = NSMenu()
let app = NSMenuItem(title: "App", action: nil, keyEquivalent: "")
app.submenu = NSMenu(); root.addItem(app)
let filter = NSMenuItem(title: "Filter", action: nil, keyEquivalent: "")
let menu = NSMenu(); menu.autoenablesItems = false; filter.submenu = menu; root.addItem(filter)
let target = Target()
for index in 0..<300 {
    let item = NSMenuItem(title: "Gaussian Blur \(index)", action: #selector(Target.run(_:)), keyEquivalent: "")
    item.target = target; menu.addItem(item)
}
var samples: [Double] = []
var count = 0
for _ in 0..<7 {
    let start = Date.timeIntervalSinceReferenceDate
    for _ in 0..<50 {
        let entries = CommandPaletteMenu.entries(in: root, skipping: [])
        count += CommandPaletteSearch.rank(entries, query: "blur").count
    }
    samples.append((Date.timeIntervalSinceReferenceDate - start) * 1000 / 50)
}
print("matched=\(count) median_ms=\(samples.sorted()[3]) samples_ms=\(samples)")
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="9a319ff", help="Git revision to compare against")
    args = parser.parse_args()
    if platform.system() != "Darwin":
        parser.error("Run on macOS with Swift and AppKit installed")
    file = "Compositor/UI/CommandPalette.swift"
    before = subprocess.check_output(["git", "show", f"{args.baseline}:{file}"], cwd=ROOT, text=True)
    after = (ROOT / file).read_text()
    with tempfile.TemporaryDirectory(prefix="compositor-palette-") as temporary:
        for label, source in [("before", before), ("after", after)]:
            path = Path(temporary) / f"{label}.swift"
            binary = Path(temporary) / label
            path.write_text(source.split("extension CommandPaletteEntry {")[0] + BENCHMARK)
            subprocess.run(["swiftc", "-O", str(path), "-o", str(binary)], check=True)
            result = subprocess.check_output([str(binary)], text=True).strip()
            print(f"{label}: {result}")


if __name__ == "__main__":
    main()
