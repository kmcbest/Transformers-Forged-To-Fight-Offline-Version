# -*- coding: utf-8 -*-
import sys
import json
import math
from pathlib import Path
import bpy
import mathutils

sys.stdout.reconfigure(encoding='utf-8')

print("=== Starting Aligned Demolishor Vehicle (Tank) Rigging ===")

bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Load the 47 vehicle bones data
with open("tools/demolishor/ironhide_47_vh_bones.json", "r", encoding="utf-8") as f:
    bones_data = json.load(f)

bone_order = bones_data["bone_order"]
bones_dict = bones_data["bones"]

def unity_pos_to_blender(u_vec):
    # Unity: X=Right, Y=Up, Z=Forward
    # Blender: X=Right, Y=Forward, Z=Up
    return mathutils.Vector((u_vec[0], u_vec[2], u_vec[1]))

# 2. Create Vehicle Armature
arm_data = bpy.data.armatures.new("character_vehicle_model")
arm_obj = bpy.data.objects.new("character_vehicle_model", arm_data)
bpy.context.scene.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')

edit_bones = {}
for name in bone_order:
    b_info = bones_dict[name]
    mat = mathutils.Matrix(b_info["matrix"])
    u_head = mat.to_translation()
    b_head = unity_pos_to_blender(u_head)
    
    eb = arm_data.edit_bones.new(name)
    eb.head = b_head
    eb.tail = b_head + mathutils.Vector((0, 0, 0.1))
    edit_bones[name] = eb

bpy.ops.object.mode_set(mode='OBJECT')
print(f"[✓] Created vehicle Armature with {len(bone_order)} bones")

# 3. Import source FBX
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

vh_mesh = bpy.data.objects.get("VH_Demolishor_SKEL.mo.dmx")
assert vh_mesh is not None, "VH_Demolishor_SKEL.mo.dmx not found in source FBX"

# Remove all other imported objects
for obj in list(bpy.data.objects):
    if obj not in [arm_obj, vh_mesh]:
        bpy.data.objects.remove(obj, do_unlink=True)

# 4. Position and orient the tank
bpy.context.view_layer.objects.active = vh_mesh
# Apply parent inverse if any
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

# Demolishor tank is facing -Y in source FBX.
# In Blender, forward facing for Unity export (with forward=-Z, up=Y) should face +Y.
# So rotate 180 deg around Z to face forward:
vh_mesh.rotation_euler = (0, 0, math.radians(180))
bpy.ops.object.transform_apply(rotation=True)

# Center tank on X and Y, set ground contact Z to 0
bbox = [mathutils.Vector(corner) for corner in vh_mesh.bound_box]
min_x = min(v.x for v in bbox)
max_x = max(v.x for v in bbox)
min_y = min(v.y for v in bbox)
max_y = max(v.y for v in bbox)
min_z = min(v.z for v in bbox)

center_x = (min_x + max_x) / 2.0
center_y = (min_y + max_y) / 2.0

vh_mesh.location.x -= center_x
vh_mesh.location.y -= center_y
vh_mesh.location.z -= min_z
bpy.ops.object.transform_apply(location=True)

# Scale slightly to match heavy combat presence
scale_val = 1.25
vh_mesh.scale = (scale_val, scale_val, scale_val)
bpy.ops.object.transform_apply(scale=True)

print(f"[✓] Tank centered and scaled (1.25x). Treads on ground Z=0.")

# 5. Bind 100% of vertices to BodyBase (the rigid chassis of the vehicle)
vh_mesh.vertex_groups.clear()
for b_name in bone_order:
    vh_mesh.vertex_groups.new(name=b_name)

bodybase_vg = vh_mesh.vertex_groups["BodyBase"]
all_vert_indices = list(range(len(vh_mesh.data.vertices)))
bodybase_vg.add(all_vert_indices, 1.0, 'REPLACE')
print(f"[✓] Assigned all {len(all_vert_indices)} vertices to 'BodyBase' with weight 1.0")

# 6. Parent mesh to Armature
vh_mesh.parent = arm_obj
mod = vh_mesh.modifiers.new(name="Armature", type='ARMATURE')
mod.object = arm_obj
mod.use_vertex_groups = True

vh_mesh.name = "cha_demolishor_gs_01"

# 7. Export FBX to Unity Project
out_fbx = Path(r"d:\Agent\tftf\toolchain\unity_build_project\Assets\Demolishor\demolishor_vh_prepared.fbx")
out_fbx.parent.mkdir(parents=True, exist_ok=True)

bpy.ops.export_scene.fbx(
    filepath=str(out_fbx),
    use_selection=False,
    bake_anim=False,
    add_leaf_bones=False,
    apply_scale_options='FBX_SCALE_ALL',
    axis_forward='-Z',
    axis_up='Y'
)

print(f"\n[✓] SUCCESS: Perfectly aligned vehicle FBX exported to {out_fbx} ({out_fbx.stat().st_size} bytes)!")
