import subprocess
from pathlib import Path

unity_exe = Path(r"E:\Agent\TFTF-blender\toolchain\Unity_2020.3.31f1\Editor\Unity.exe")
project_dir = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project")
log_file = project_dir / "unity_render.log"

cmd = [
    str(unity_exe),
    "-batchmode",
    "-quit",
    "-projectPath", str(project_dir),
    "-executeMethod", "RenderToxitronPreview.Render",
    "-logFile", str(log_file)
]

print(f"Running: {' '.join(cmd)}")
res = subprocess.run(cmd, timeout=120)
print(f"Unity exit code: {res.returncode}")

brain_dir = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\76f5ec0f-a15b-490d-aeb0-5237fdbedbfa")
preview_file = brain_dir / "toxitron_preview.png"
if preview_file.exists():
    print(f"[OK] Preview generated at: {preview_file} ({preview_file.stat().st_size} bytes)")
else:
    print("Preview file was not found!")
