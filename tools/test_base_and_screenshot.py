import subprocess
import time
import os

pkg = "com.kabam.tftf"
artifact_dir = r"C:\Users\Xiangli496\.gemini\antigravity\brain\2930ed50-f13f-400a-a054-1cc5d63aea4b"
screenshot_path = os.path.join(artifact_dir, "base_screen.png")

print("Stopping app...")
subprocess.run(["adb", "shell", "am", "force-stop", pkg])
time.sleep(1)
subprocess.run(["adb", "logcat", "-c"])

print("Launching app...")
subprocess.run(["adb", "shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"])

print("Waiting 18 seconds for game to boot and load base...")
for i in range(18):
    time.sleep(1)
    if (i + 1) % 5 == 0:
        print(f"  {i + 1}s elapsed...")

print("Dumping logcat lines related to base and hook...")
p = subprocess.run(["adb", "logcat", "-d"], capture_output=True, text=True, errors="ignore")
keywords = ["BASEDIAG", "BASEAPPLY", "BaseBoard", "BaseNode", "GameboardBuilder", "library_primordial", "TFTFHOOK", "getBaseHeroData", "/base/active"]
for l in p.stdout.splitlines():
    if any(k in l for k in keywords):
        print(l)

print("Capturing screenshot...")
subprocess.run(["adb", "shell", "screencap", "-p", "/sdcard/base_screen.png"])
subprocess.run(["adb", "pull", "/sdcard/base_screen.png", screenshot_path])
print(f"Screenshot saved to: {screenshot_path}")
