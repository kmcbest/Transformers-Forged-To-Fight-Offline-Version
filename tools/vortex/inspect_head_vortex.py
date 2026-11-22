import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
import UnityPy
import numpy as np
from PIL import Image
import os

head_path = r"e:\Agent\TFTF-blender\tools\vortex\vortex_gs_head.assetbundle"
raw_bundle = subprocess.check_output(
    ["git", "show", "HEAD:assets_redeco/vortex_gs.assetbundle"],
    cwd=r"e:\Agent\TFTF-blender"
)
with open(head_path, "wb") as f:
    f.write(raw_bundle)
print(f"Extracted HEAD bundle cleanly: {len(raw_bundle):,} bytes")

env = UnityPy.load(head_path)
obj_map = {obj.path_id: obj for obj in env.objects}

print("\n=== Texture2D List ===")
for obj in env.objects:
    if obj.type.name == "Texture2D":
        t = obj.read()
        tt = obj.read_typetree()
        print(f"  Tex {t.m_Name} (PID {obj.path_id}): {t.m_Width}x{t.m_Height}, fmt={t.m_TextureFormat}, mips={tt.get('m_MipCount')}")

print("\n=== Material List (Character/Weapon/Vehicle) ===")
for obj in env.objects:
    if obj.type.name == "Material":
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        if not name.startswith("fx_"):
            print(f"  Mat {name} (PID {obj.path_id}), shader={tt.get('m_Shader')}")
            for te in tt["m_SavedProperties"]["m_TexEnvs"]:
                tex_pid = te[1]["m_Texture"]["m_PathID"]
                tex_name = obj_map[tex_pid].read().m_Name if tex_pid in obj_map else str(tex_pid)
                if tex_pid != 0:
                    print(f"    Tex {te[0]} -> {tex_name} ({tex_pid})")
            for c in tt["m_SavedProperties"]["m_Colors"]:
                if c[0] in ("_Color", "_base_col", "_emissive_intensity_col"):
                    print(f"    Col {c[0]} -> {c[1]}")
            for f in tt["m_SavedProperties"]["m_Floats"]:
                if "emissive" in f[0].lower():
                    print(f"    Float {f[0]} -> {f[1]}")

print("\n=== SMR List ===")
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tt = obj.read_typetree()
        mpid = tt["m_Mesh"]["m_PathID"]
        mname = obj_map[mpid].read().m_Name if mpid in obj_map else str(mpid)
        mats = [m["m_PathID"] for m in tt["m_Materials"]]
        print(f"  SMR {obj.path_id}: enabled={tt.get('m_Enabled')}, mesh={mname} ({mpid}), mats={mats}")
