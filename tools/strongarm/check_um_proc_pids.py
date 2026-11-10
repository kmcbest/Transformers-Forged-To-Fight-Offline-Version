import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p_proc = Path(r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle")
env_proc = UnityPy.load(str(p_proc))

for obj in env_proc.objects:
    if obj.type.name == "AnimationClip":
        d = obj.read()
        name = getattr(d, 'name', '') or getattr(d, 'm_Name', '')
        if "ultramagnus" in name.lower() and "victory" in name.lower():
            print(f"Proc clip: '{name}' -> PID {obj.path_id}")
