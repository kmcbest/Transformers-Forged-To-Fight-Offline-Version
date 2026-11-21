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

def vg_stats(name):
    vg = mesh.vertex_groups.get(name)
    if not vg:
        print(f"VG {name}: NOT FOUND")
        return
    pts = [mesh.matrix_world @ v.co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.5 for g in v.groups)]
    if pts:
        min_x = min(p.x for p in pts)
        max_x = max(p.x for p in pts)
        min_z = min(p.z for p in pts)
        max_z = max(p.z for p in pts)
        print(f"VG {name}: count={len(pts)}, X=[{min_x:.3f}, {max_x:.3f}], Z=[{min_z:.3f}, {max_z:.3f}]")

for name in ["Bone_L_Clavicle01", "Bone_L_Clavicle02", "Bone_L_UpperArm", "Bone_R_Clavicle01", "Bone_R_Clavicle02", "Bone_R_UpperArm"]:
    vg_stats(name)
