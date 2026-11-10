import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p_prowl = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
env_prowl = UnityPy.load(str(p_prowl))

for obj in env_prowl.objects:
    if obj.type.name == "AnimatorOverrideController":
        tree = obj.read_typetree()
        if "fight" in tree.get("m_Name", "").lower():
            for pair in tree.get("m_Clips", []):
                orig = pair.get("m_OriginalClip", {})
                over = pair.get("m_OverrideClip", {})
                if orig.get("m_PathID") in (3642901185112467297, -4048722777385356729):
                    print(f"Orig: {orig} -> Over: {over}")
