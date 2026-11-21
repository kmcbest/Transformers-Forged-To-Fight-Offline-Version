import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion, Euler
import math

ROOT = Path("e:/Agent/TFTF-blender")
FBX_SRC = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")

print("=== 1. Check all objects and Shadow/Symbol ===")
for o in bpy.data.objects:
    print(f"  Obj: {o.name} (type={o.type}, verts={len(o.data.vertices) if o.type=='MESH' else 0})")

print("\n=== 2. Check Vehicle Idle01 Wing & Beak Bone Locations & Rest Offsets ===")
act_v = bpy.data.actions.get("Bip001|vehicle_idle01|Base Layer")
arm.animation_data.action = act_v
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()

deps = bpy.context.evaluated_depsgraph_get()
ev_mesh = mesh.evaluated_get(deps)

def eval_bounds(vg_name):
    vg = mesh.vertex_groups.get(vg_name)
    if not vg: return None
    pts = [ev_mesh.matrix_world @ ev_mesh.data.vertices[v.index].co
           for v in mesh.data.vertices
           if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
    if not pts: return None
    return (
        min(p.x for p in pts), max(p.x for p in pts),
        min(p.y for p in pts), max(p.y for p in pts),
        min(p.z for p in pts), max(p.z for p in pts),
    )

for vn in ["Back", "Bone_L_Wing_01(mirrored)", "Bone_L_Wing_02(mirrored)", "Bone_R_Wing_01", "Bone_R_Wing_02", "bird_Head", "beak", "beak_the bottom", "Bone_Pelvis"]:
    b = eval_bounds(vn)
    print(f"  {vn:26s}: {tuple(round(x, 4) for x in b) if b else None}")

# Check why Bone_L_Wing_02 separated from Wing_01
for bn in ["Back", "Bone_L_Wing_01(mirrored)", "Bone_L_Wing_02(mirrored)", "bird_Head", "beak_the bottom"]:
    b = arm.data.bones.get(bn)
    pb = arm.pose.bones.get(bn)
    if b and pb:
        print(f"  Bone {bn:26s}: rest_head={tuple(round(x,4) for x in b.head_local)}, pb.head={tuple(round(x,4) for x in pb.head)}, pb.loc={tuple(round(x,4) for x in pb.location)}, pb.rot={tuple(round(x,4) for x in pb.rotation_quaternion)}")
