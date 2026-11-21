import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
from mathutils import Quaternion, Vector, Euler
import math

FBX_SRC = Path("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")

arm.animation_data_clear()
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.transforms_clear()

# Let's test rotating Bone_R_Finger1 by Euler Z = +45 deg vs -45 deg
pb = arm.pose.bones["Bone_R_Finger1"]
pb.rotation_mode = 'XYZ'
pb.rotation_euler = Euler((0, 0, math.radians(45)), 'XYZ')

pb11 = arm.pose.bones["Bone_R_Finger11"]
pb11.rotation_mode = 'XYZ'
pb11.rotation_euler = Euler((0, 0, math.radians(45)), 'XYZ')

pb12 = arm.pose.bones["Bone_R_Finger12"]
pb12.rotation_mode = 'XYZ'
pb12.rotation_euler = Euler((0, 0, math.radians(45)), 'XYZ')

bpy.ops.object.mode_set(mode='OBJECT')

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = mesh.evaluated_get(depsgraph)
eval_mesh = eval_obj.to_mesh()

vg = mesh.vertex_groups.get("Bone_R_Finger12")
pts_raw = [mesh.data.vertices[v.index].co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.5 for g in v.groups)]
pts_curled = [eval_mesh.vertices[v.index].co for v in eval_mesh.vertices if any(g.group == vg.index and g.weight > 0.5 for g in v.groups)]

print(f"Right Index fingertip (45 deg +Z):")
print(f"  Raw Z: [{min(p.z for p in pts_raw):.4f}, {max(p.z for p in pts_raw):.4f}], Y: [{min(p.y for p in pts_raw):.4f}, {max(p.y for p in pts_raw):.4f}]")
print(f"  Curled Z: [{min(p.z for p in pts_curled):.4f}, {max(p.z for p in pts_curled):.4f}], Y: [{min(p.z for p in pts_curled):.4f}, {max(p.y for p in pts_curled):.4f}]")
