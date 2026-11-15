import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy
import numpy as np

ROOT = Path(r"E:\Agent\TFTF-blender")
MEG_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_gs_leader2015_odr" / "megatron_gs_leader2015.assetbundle"
env = UnityPy.load(str(MEG_BUNDLE))

# Map Transform path_id -> GameObject Name
go_names = {}
transforms = {}
for obj in env.objects:
    if obj.type.name == "GameObject":
        d = obj.read()
        go_names[obj.path_id] = d.m_Name
    elif obj.type.name == "Transform":
        t = obj.read_typetree()
        transforms[obj.path_id] = t

tr_to_name = {}
for tr_id, tr in transforms.items():
    go_id = tr.get("m_GameObject", {}).get("m_PathID")
    tr_to_name[tr_id] = go_names.get(go_id, f"Unknown_{go_id}")

print("=== Megatron Transform Local Rotations ===")
for tr_id, tr in transforms.items():
    name = tr_to_name.get(tr_id, "")
    if any(k in name for k in ["Thumb", "Index"]):
        rot = tr.get("m_LocalRotation", {})
        pos = tr.get("m_LocalPosition", {})
        print(f"Transform '{name:20s}': localPos=({pos.get('x',0):7.4f}, {pos.get('y',0):7.4f}, {pos.get('z',0):7.4f}) localRot=(w={rot.get('w',0):7.4f}, x={rot.get('x',0):7.4f}, y={rot.get('y',0):7.4f}, z={rot.get('z',0):7.4f})")
