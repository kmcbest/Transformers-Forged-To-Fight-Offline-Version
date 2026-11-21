import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
from mathutils import Vector, Matrix

FBX_SRC = Path("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

mesh = bpy.data.objects.get("Swoop.001")
vs = [v.co for v in mesh.data.vertices]
min_z, max_z = min(v.z for v in vs), max(v.z for v in vs)
raw_h = max_z - min_z
scale_factor = 11.40 / raw_h

def get_scaled_z_bounds(vg_name):
    vg = mesh.vertex_groups.get(vg_name)
    pts = [v.co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
    if not pts: return None
    zs = [(p.z - min_z) * scale_factor for p in pts]
    return (min(zs), max(zs))

print(f"Scale factor: {scale_factor:.4f}")
print(f"Bone_L_Forearm Z: {get_scaled_z_bounds('Bone_L_Forearm')}")
print(f"Bone_L_Hand Z: {get_scaled_z_bounds('Bone_L_Hand')}")
print(f"Bone_L_Finger1 Z: {get_scaled_z_bounds('Bone_L_Finger1')}")
print(f"Bone_L_Finger12 Z: {get_scaled_z_bounds('Bone_L_Finger12')}")
