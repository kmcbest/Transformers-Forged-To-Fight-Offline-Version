import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
from mathutils import Vector

FBX_SRC = Path("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

mesh = bpy.data.objects.get("Swoop.001")
arm = bpy.data.objects.get("Bip001")

def get_vg_bounds(name):
    vg = mesh.vertex_groups.get(name)
    if not vg: return None
    pts = [v.co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
    if not pts: return None
    return (min(p.z for p in pts), max(p.z for p in pts))

print("Z bounds in Raw Static Pose:")
print(f"  Bone_L_Forearm: {get_vg_bounds('Bone_L_Forearm')}")
print(f"  Bone_L_Hand: {get_vg_bounds('Bone_L_Hand')}")
print(f"  Bone_L_Finger1: {get_vg_bounds('Bone_L_Finger1')}")
print(f"  Bone_L_Finger12: {get_vg_bounds('Bone_L_Finger12')}")
print(f"  Bone_R_Forearm: {get_vg_bounds('Bone_R_Forearm')}")
print(f"  Bone_R_Hand: {get_vg_bounds('Bone_R_Hand')}")
print(f"  Bone_R_Finger1: {get_vg_bounds('Bone_R_Finger1')}")
print(f"  Bone_R_Finger12: {get_vg_bounds('Bone_R_Finger12')}")
