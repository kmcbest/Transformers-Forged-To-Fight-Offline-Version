import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
from pathlib import Path

scratch = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch")

# Pull full logcat across main + system + crash and search for com.kabam.bigrobot / Unity / DOTHOOK / FATAL
res = subprocess.run(["adb", "logcat", "-b", "all", "-d"], capture_output=True, text=True, encoding="utf-8", errors="replace")
lines = res.stdout.splitlines()
print(f"Total logcat lines: {len(lines)}")

hits = []
for i, l in enumerate(lines):
    low = l.lower()
    if any(k in low for k in ("bigrobot", "dothook", "unity", "il2cpp", "strongarm", "fatal", "sigsegv", "sigabrt", "exception")):
        if "dex2oat" not in low and "kingsoft" not in low and "resolv" not in low and "mdns" not in low:
            hits.append((i, l))

out = scratch / "bigrobot_all.log"
out.write_text("\n".join(l for _, l in hits), encoding="utf-8")
print(f"Matched {len(hits)} relevant lines -> {out}")
for _, l in hits[-120:]:
    print(l)
