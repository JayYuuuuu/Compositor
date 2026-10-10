#!/usr/bin/env python3
"""Verify the actual Release app starts and creates a window. Requires a logged-in macOS desktop."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import time

PROBE = """
import AppKit
import CoreGraphics
import Foundation
let pid = Int32(CommandLine.arguments[1])!
let application = NSRunningApplication(processIdentifier: pid)
let windows = CGWindowListCopyWindowInfo(.excludeDesktopElements, kCGNullWindowID) as? [[String: Any]] ?? []
let owned = windows.filter { ($0[kCGWindowOwnerPID as String] as? Int) == Int(pid) && ($0[kCGWindowLayer as String] as? Int) == 0 }
let value: [String: Any] = ["finished_launching": application?.isFinishedLaunching ?? false,
                          "window_count": owned.count]
print(String(data: try! JSONSerialization.data(withJSONObject: value), encoding: .utf8)!)
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--app', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    binary = args.app / 'Contents/MacOS/Compositor CN'
    with tempfile.TemporaryDirectory(prefix='CompositorReleaseLaunch-') as folder:
        folder = Path(folder)
        probe = folder / 'Probe.swift'; probe.write_text(PROBE)
        subprocess.run(['xcrun', 'swiftc', str(probe), '-o', str(folder / 'probe')], check=True)
        start = time.monotonic()
        with (folder / 'stdout.log').open('w') as out, (folder / 'stderr.log').open('w') as err:
            process = subprocess.Popen([str(binary), '-SUEnableAutomaticChecks', 'NO',
                '-SUHasLaunchedBefore', 'YES', '-ApplePersistenceIgnoreState', 'YES'],
                stdout=out, stderr=err)
            try:
                time.sleep(8)
                if process.poll() is not None:
                    raise RuntimeError('Release app exited during startup; exit=' + str(process.returncode))
                result = subprocess.run([str(folder / 'probe'), str(process.pid)], capture_output=True, text=True, check=True)
                evidence = json.loads(result.stdout)
                if not evidence['finished_launching'] or evidence['window_count'] < 1:
                    raise RuntimeError('Release app did not finish launching and create an editor window')
                evidence.update(status='passed', seconds=round(time.monotonic() - start, 3))
                args.output.write_text(json.dumps(evidence, indent=2) + '\n')
                print(json.dumps(evidence))
            finally:
                if process.poll() is None:
                    process.terminate()
                    try: process.wait(timeout=10)
                    except subprocess.TimeoutExpired: process.kill(); process.wait()

if __name__ == '__main__':
    main()
