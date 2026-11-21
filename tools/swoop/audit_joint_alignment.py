import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path("e:/Agent/TFTF-blender")
BP_JSON = ROOT / "tools/swoop/ramjet_78_authoritative_bindposes.json"
FBX_SRC = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"

with open(BP_JSON, "r", encoding="utf-8") as f:
    ramjet_data = json.load(f)["bones"]

def r_pos(bname):
    ux, uy, uz = ramjet_data[bname]["unity_world_pos"]
    return Vector((-ux, -uz, uy)) # Blender (X, Y, Z)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

mesh = bpy.data.objects.get("Swoop.001")
arm = bpy.data.objects.get("Bip001")

vs = [v.co for v in mesh.data.vertices]
min_z = min(v.z for v in vs)
max_z = max(v.z for v in vs)
raw_h = max_z - min_z
old_scale = 11.40 / raw_h

print(f"Raw min_z={min_z:.4f}, max_z={max_z:.4f}, raw_h={raw_h:.4f}, old_scale={old_scale:.4f}")

def vg_center(vg_name, scale):
    vg = mesh.vertex_groups.get(vg_name)
    if not vg: return None
    pts = [v.co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
    if not pts: return None
    cx = sum(p.x for p in pts) / len(pts) * scale
    cy = sum(p.y for p in pts) / len(pts) * scale
    cz = (sum(p.z for p in pts) / len(pts) - min_z) * scale
    min_pz = (min(p.z for p in pts) - min_z) * scale
    max_pz = (max(p.z for p in pts) - min_z) * scale
    return (cx, cy, cz, min_pz, max_pz)

pairs = [
    ("Bip001 Head", "Head"),
    ("Bone_L_UpperArm", "LeftArm"),
    ("Bone_L_Forearm", "LeftForeArm"),
    ("Bone_L_Hand", "LeftHand"),
    ("Bone_Pelvis", "Hips"),
    ("Bone_L_Thigh", "LeftUpLeg"),
    ("Bone_L_Calf", "LeftLeg"),
    ("Bone_L_Foot00", "LeftFoot"),
]

print("\n=== Joint Comparison at old_scale (3.2659) ===")
for s_vg, r_bone in pairs:
    sc = vg_center(s_vg, old_scale)
    rp = r_pos(r_bone)
    if sc:
        print(f"  {s_vg:18s} -> Z_mean={sc[2]:6.3f} (Z=[{sc[3]:5.2f}, {sc[4]:5.2f}]), X_mean={sc[0]:+6.3f} | Ramjet {r_bone:12s}: Z={rp.z:6.3f}, X={rp.x:+6.3f}")
