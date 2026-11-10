import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
from pathlib import Path

out_log = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch\device_crash.log")

res_crash = subprocess.run(["adb", "logcat", "-b", "crash", "-d"], capture_output=True, text=True, encoding="utf-8", errors="replace")
res_main = subprocess.run(["adb", "logcat", "-b", "main", "-d", "-t", "5000"], capture_output=True, text=True, encoding="utf-8", errors="replace")

lines = res_main.stdout.splitlines()
filtered = [l for l in lines if any(k in l.lower() for k in ("bigrobot", "unity", "il2cpp", "dothook", "strongarm", "prowl", "fatal", "sigsegv", "sigabrt", "exception", "error", "assert", "bundle", "prefab", "combat", "fight"))]

text = "=== CRASH BUFFER ===\n" + res_crash.stdout + "\n\n=== FILTERED MAIN LOG (last 200 matches) ===\n" + "\n".join(filtered[-200:])
out_log.write_text(text, encoding="utf-8")
print(f"Wrote {out_log} ({len(res_crash.stdout)} crash chars, {len(filtered)} main matches)")
print("=== CRASH BUFFER PREVIEW ===")
print(res_crash.stdout[-2500:])
print("=== LAST 40 FILTERED MAIN LINES ===")
print("\n".join(filtered[-40:]))
