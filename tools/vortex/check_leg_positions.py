import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import json
import math
import mathutils
from pathlib import Path

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vortex_master.blend")
arm = bpy.data.objects["Vortex_ARM"]
scale_factor = 2.05
arm.scale = (scale_factor, scale_factor, scale_factor)
arm.rotation_euler = (0, 0, math.radians(90.0))
bpy.context.view_layer.update()

bp_data = json.loads(Path(r"E:\Agent\TFTF-blender\tools\vortex\grindor_78_authoritative_bindposes.json").read_text(encoding="utf-8"))
g_b_pos = {}
for bname, info in bp_data.items():
    p = info["world_pos"]
    g_b_pos[bname] = mathutils.Vector((p["x"], p["z"], p["y"]))

print("=== Grindor Leg / Foot Positions (Blender) ===")
for b in ["LeftUpLeg", "LeftLeg", "LeftFoot", "RightUpLeg", "RightLeg", "RightFoot"]:
    p = g_b_pos[b]
    print(f"  {b:12s}: ({p.x:6.3f}, {p.y:6.3f}, {p.z:6.3f})")

print("\n=== Vortex Raw Leg / Foot Positions (Blender, Rotated + Scaled) ===")
for b, gb in [("bip_hip_L", "LeftUpLeg"), ("bip_knee_L", "LeftLeg"), ("bip_foot_L", "LeftFoot"),
              ("bip_hip_R", "RightUpLeg"), ("bip_knee_R", "RightLeg"), ("bip_foot_R", "RightFoot")]:
    p = (arm.matrix_world @ arm.data.bones[b].head_local)
    print(f"  {b:12s}: ({p.x:6.3f}, {p.y:6.3f}, {p.z:6.3f})  [target: {gb} Z={g_b_pos[gb].z:6.3f}]")

# Check mesh ground contact
head_mesh = bpy.data.objects["RB_Vortex_CHARSKEL_Head.mo.dmx"]
zs = [(arm.matrix_world @ v.co).z for v in head_mesh.data.vertices]
print(f"\nMesh min Z: {min(zs):.3f}, max Z: {max(zs):.3f}")
