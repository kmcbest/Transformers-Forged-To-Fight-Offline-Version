import subprocess
import json
import re

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return res.stdout.strip()

print("ADB Devices:")
print(run_cmd("adb devices"))

print("\nPackage info for com.kabam.bigrobot:")
pkg_dump = run_cmd("adb shell dumpsys package com.kabam.bigrobot")
for line in pkg_dump.splitlines():
    if any(k in line for k in ["versionName", "versionCode", "firstInstallTime", "lastUpdateTime"]):
        print(line.strip())

print("\nProcess check:")
ps = run_cmd("adb shell ps -ef | grep kabam")
print(ps)
