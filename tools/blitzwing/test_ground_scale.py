import sys
from pathlib import Path
import math
import bpy
import bmesh
import mathutils
from mathutils import Vector, Matrix, Quaternion
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_DIR = ROOT / "3rd-party-models" / "Blitzwing_EW" / "01_source"
MEG_51_JSON = ROOT / "tools" / "blitzwing" / "megatron_51_authoritative_bindposes.json"
meg_51_data = json.loads(MEG_51_JSON.read_text(encoding="utf-8"))

def u_to_b(pos):
    return Vector((-float(pos[0]), -float(pos[2]), float(pos[1])))

meg_b_pos = {b: u_to_b(meg_51_data["bones"][b]["unity_world_pos"]) for b in meg_51_data["bones"]}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_M_LOD.fbx"))

mesh_obj = bpy.data.objects['H_shandian_G1_M_Lod']
arm_obj = bpy.data.objects['floor']

# 1. Unparent keeping transform
bpy.ops.object.select_all(action='DESELECT')
for o in [mesh_obj, arm_obj]:
    o.select_set(True)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

# Remove all other objects
for o in list(bpy.data.objects):
    if o not in [mesh_obj, arm_obj]:
        bpy.data.objects.remove(o, do_unlink=True)

# 2. Reset rest pose & clear animations
arm_obj.animation_data_clear()
mesh_obj.animation_data_clear()
for pb in arm_obj.pose.bones:
    pb.location = (0, 0, 0)
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.rotation_euler = (0, 0, 0)
    pb.scale = (1, 1, 1)
arm_obj.data.pose_position = 'REST'
bpy.context.view_layer.update()

# 3. Apply all initial transforms
bpy.ops.object.select_all(action='DESELECT')
for o in [mesh_obj, arm_obj]:
    o.select_set(True)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 4. Ground Z=0
min_z = min(v.co.z for v in mesh_obj.data.vertices)
print(f"Grounding by {-min_z:.4f}m...")
mesh_obj.location.z -= min_z
arm_obj.location.z -= min_z
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 5. Scale to Megatron height
SCALE = 149.1728
mesh_obj.scale = (SCALE, SCALE, SCALE)
arm_obj.scale = (SCALE, SCALE, SCALE)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Check bounds after scale
zs = [v.co.z for v in mesh_obj.data.vertices]
head_bone = arm_obj.data.bones["Bip001 Head"]
print(f"After Ground & Scale:")
print(f"  Mesh Z bounds: [{min(zs):.3f}, {max(zs):.3f}]m")
print(f"  Head bone head: {head_bone.head_local}")
assert abs(min(zs)) < 0.05, f"Min Z {min(zs)} not grounded!"
assert abs(head_bone.head_local.z - 10.099) < 0.1, f"Head Z {head_bone.head_local.z} not aligned to 10.099m!"
print("[PASS] Ground & Scale verified perfectly!")
