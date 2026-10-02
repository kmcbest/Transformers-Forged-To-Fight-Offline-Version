from pathlib import Path
import os

appdata = os.environ.get("LOCALAPPDATA", "")
log_path = Path(appdata) / "Unity" / "Editor" / "Editor.log"

print(f"Log path: {log_path}, exists: {log_path.exists()}")
if log_path.exists():
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    print(f"Total lines in Editor.log: {len(lines)}")
    # Print the last 100 lines
    for line in lines[-120:]:
        print(line)
