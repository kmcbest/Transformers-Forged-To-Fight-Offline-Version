import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\Materials")
for mat_file in ROOT.glob("*.mat"):
    text = mat_file.read_text(encoding="utf-8", errors="replace")
    print(f"=== {mat_file.name} ===")
    for line in text.splitlines():
        if "_base_tex" in line or "_MainTex" in line or "m_Texture" in line or "_Color" in line:
            print(" ", line[:100])
