import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
env = UnityPy.load(str(ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle"))
sf = list(env.assets)[0]

pid = -8455018533602519118
print(f"Is Necrotronus idle PID {pid} in Sideswipe bundle? {pid in sf.objects}")
