import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import math
from pathlib import Path
import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

ROOT = Path("e:/Agent/TFTF-blender")
FBX_SRC = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"
OUT_IMG = ROOT / "renders/swoop/debug_blender_fists.png"
OUT_IMG.parent.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")

# Clear anim and reset pose
arm.animation_data_clear()
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.transforms_clear()

# Check exact bounds of Hand vs Forearm before adjustment
bpy.ops.object.mode_set(mode='OBJECT')
def vg_z_range(vgn):
    vg = mesh.vertex_groups[vgn]
    pts = [mesh.matrix_world @ v.co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
    return min(p.z for p in pts), max(p.z for p in pts)

# Wait: in Swoop_pbr.fbx, mesh.matrix_world is 0.01 scale; check local mesh space!
def vg_local_bounds(vgn):
    vg = mesh.vertex_groups[vgn]
    pts = [v.co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
    return (
        (min(p.x for p in pts), max(p.x for p in pts)),
        (min(p.y for p in pts), max(p.y for p in pts)),
        (min(p.z for p in pts), max(p.z for p in pts)),
    )

print("Raw Local Bounds:")
for vn in ["Bone_L_Forearm", "Bone_L_Hand", "Bone_L_Finger02", "Bone_L_Finger12", "Bone_L_Finger22",
           "Bone_R_Forearm", "Bone_R_Hand", "Bone_R_Finger02", "Bone_R_Finger12", "Bone_R_Finger22"]:
    print(f"  {vn:16s}: {vg_local_bounds(vn)}")

# Also check Bone_L_Clavicle01, Clavicle02, UpperArm, Symbol_AB
for vn in ["Bone_L_Clavicle01", "Bone_L_Clavicle02", "Bone_L_UpperArm"]:
    print(f"  {vn:16s}: {vg_local_bounds(vn)}")
sym = bpy.data.objects.get("Symbol_AB")
if sym:
    pts = [v.co for v in sym.data.vertices]
    print(f"  Symbol_AB       : X=({min(p.x for p in pts):.3f},{max(p.x for p in pts):.3f}), Y=({min(p.y for p in pts):.3f},{max(p.y for p in pts):.3f}), Z=({min(p.z for p in pts):.3f},{max(p.z for p in pts):.3f})")
    bchest = vg_local_bounds("bird_chest")
    print(f"  bird_chest      : X=({bchest[0][0]:.3f},{bchest[0][1]:.3f}), Y=({bchest[1][0]:.3f},{bchest[1][1]:.3f}), Z=({bchest[2][0]:.3f},{bchest[2][1]:.3f})")
