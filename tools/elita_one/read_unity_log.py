import os
from pathlib import Path

appdata = os.environ.get("LOCALAPPDATA")
log_path = Path(appdata) / "Unity" / "Editor" / "Editor.log"
if log_path.exists():
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    print(f"Total lines in Editor.log: {len(lines)}")
    for l in lines[-35:]:
        print(l)
else:
    print("Editor.log not found at:", log_path)
