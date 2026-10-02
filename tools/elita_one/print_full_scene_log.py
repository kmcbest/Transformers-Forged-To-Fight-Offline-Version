from pathlib import Path

log_path = Path("toolchain/unity_build_project/debug_scene.log")
if log_path.exists():
    text = log_path.read_text(encoding="utf-8", errors="replace")
    print(text)
else:
    print("No debug_scene.log")
