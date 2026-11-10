import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import bmesh
import json
import math
import numpy as np
from pathlib import Path

print("=== [Strongarm] Generating 1:1 Aligned Grafted Vehicle FBX for Prowl Chassis ===")

obj_path = Path(r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.obj")
prowl_vh_rig_path = Path(r"E:\Agent\TFTF-blender\tools\strongarm\prowl_vehicle_rig.json")
out_fbx_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\strongarm_vh_prepared.fbx")
out_fbx_path.parent.mkdir(parents=True, exist_ok=True)

# 1. Load Prowl vehicle rig
with open(prowl_vh_rig_path, "r", encoding="utf-8") as f:
    prowl_vh_bones = json.load(f)

# Blender coordinates: Unity negates X on import (X_unity = -X_blender)
# Therefore in Blender: X = -ux, Y = uz (Forward), Z = uy (Height)
prowl_vh_bone_positions = {}
for b in prowl_vh_bones:
    bp = b["bindpose"]
    mat = np.array([
        [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
        [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
        [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
        [bp['e30'], bp['e31'], bp['e32'], bp['e33']]
    ])
    inv = np.linalg.inv(mat)
    ux = inv[0, 3]
    uy = inv[1, 3]
    uz = inv[2, 3]
    # Blender: X = -ux, Y = uz, Z = uy
    prowl_vh_bone_positions[b["name"]] = (-ux, uz, uy)

# 2. Import Strongarm vehicle OBJ
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(obj_path))

car = bpy.data.objects['strongarm_vehicle']
bpy.context.view_layer.objects.active = car

# Step A: Rotate +90 deg around X so Y_obj (height) becomes +Z (height), then +180 deg around Z
# so raw +Z_obj (Strongarm truck front bumper/grille) aligns to Blender +Y (Unity +Z Front, matching Prowl).
car.rotation_euler = (math.pi / 2.0, 0.0, 0.0)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
car.rotation_euler = (0.0, 0.0, math.pi)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Step B: Apply uniform scale so wheels remain 100% circular and pickup truck proportions stay natural
s_vh = 1.18
car.scale = (s_vh, s_vh, s_vh)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Step B2: Weld 478 fragmented OBJ strips while keeping loop UVs intact,
# clear broken custom split normals, recalculate consistent outward faces, and apply Auto Smooth
import bmesh
bm_weld = bmesh.new()
bm_weld.from_mesh(car.data)
bmesh.ops.remove_doubles(bm_weld, verts=bm_weld.verts, dist=0.0002)
bmesh.ops.recalc_face_normals(bm_weld, faces=bm_weld.faces)
bm_weld.to_mesh(car.data)
bm_weld.free()
if car.data.has_custom_normals:
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
    bpy.ops.object.mode_set(mode='OBJECT')
car.data.polygons.foreach_set("use_smooth", [True] * len(car.data.polygons))
car.data.use_auto_smooth = True
car.data.auto_smooth_angle = 0.66
car.data.update()

# Separate loose parts to identify the 4 wheels cleanly
bpy.ops.mesh.separate(type='LOOSE')
parts = [o for o in bpy.data.objects if o.type == 'MESH']
print(f"Imported vehicle with {len(parts)} loose parts.")

# 4 Wheel axle centers in Blender space after Z-180 alignment (+Y = Front) & uniform scale s_vh=1.18:
# Raw OBJ wheel centers: (±1.128, Front +1.877 / Rear -1.672, +0.564)
# Bind all 4 wheels to CenterBackCarFront so they stay locked inside pickup wheel arches across all clips.
wheel_configs = [
    ("FrontLeft",   1.128 * s_vh,  1.877 * s_vh, 0.564 * s_vh, "CenterBackCarFront"),
    ("FrontRight", -1.128 * s_vh,  1.877 * s_vh, 0.564 * s_vh, "CenterBackCarFront"),
    ("RearLeft",    1.128 * s_vh, -1.672 * s_vh, 0.564 * s_vh, "CenterBackCarFront"),
    ("RearRight",  -1.128 * s_vh, -1.672 * s_vh, 0.564 * s_vh, "CenterBackCarFront"),
]

wheel_parts = {wc[0]: [] for wc in wheel_configs}
body_parts = []

for p in parts:
    verts = p.data.vertices
    cx = sum(v.co.x for v in verts) / len(verts)
    cy = sum(v.co.y for v in verts) / len(verts)
    cz = sum(v.co.z for v in verts) / len(verts)
    
    matched_wheel = None
    for name, wx, wy, wz, bone in wheel_configs:
        dist_yz = math.sqrt((cy - wy)**2 + (cz - wz)**2)
        dist_x = abs(cx - wx)
        if dist_yz < 0.70 and dist_x < 0.45:
            matched_wheel = name
            break
            
    if matched_wheel:
        wheel_parts[matched_wheel].append(p)
    else:
        body_parts.append(p)

for wc in wheel_configs:
    wname = wc[0]
    print(f"Wheel '{wname}': {len(wheel_parts[wname])} sub-parts.")
print(f"Body: {len(body_parts)} sub-parts.")

# Join each wheel's subparts and apply radial subdivision & smoothing
smoothed_wheels = []
for name, wx, wy, wz, bone in wheel_configs:
    w_objs = wheel_parts[name]
    if not w_objs:
        continue
    bpy.ops.object.select_all(action='DESELECT')
    for o in w_objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = w_objs[0]
    bpy.ops.object.join()
    w_joined = bpy.context.view_layer.objects.active
    w_joined.name = f"Wheel_{name}"

    bm = bmesh.new()
    bm.from_mesh(w_joined.data)
    
    rim_verts = [v for v in bm.verts if abs(v.co.x - wx) < 0.25]
    print(f"Wheel {name}: total verts = {len(bm.verts)}, rim/tread verts = {len(rim_verts)}")
    
    for v in rim_verts:
        dy = v.co.y - wy
        dz = v.co.z - wz
        r = math.sqrt(dy**2 + dz**2)
        if 0.35 < r < 0.65:
            target_r = 0.50
            blend = 0.65
            new_r = r * (1.0 - blend) + target_r * blend
            angle = math.atan2(dz, dy)
            v.co.y = wy + new_r * math.cos(angle)
            v.co.z = wz + new_r * math.sin(angle)
            
    bm.to_mesh(w_joined.data)
    bm.free()
    
    sub_mod = w_joined.modifiers.new(name="Subsurf", type='SUBSURF')
    sub_mod.levels = 1
    sub_mod.render_levels = 1
    sub_mod.subdivision_type = 'CATMULL_CLARK'
    bpy.ops.object.modifier_apply(modifier=sub_mod.name)
    
    w_joined.vertex_groups.clear()
    vg = w_joined.vertex_groups.new(name=bone)
    vg.add(list(range(len(w_joined.data.vertices))), 1.0, 'REPLACE')
    
    smoothed_wheels.append(w_joined)

# Join body parts
bpy.ops.object.select_all(action='DESELECT')
for p in body_parts:
    p.select_set(True)
bpy.context.view_layer.objects.active = body_parts[0]
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = "Vehicle_Body"

body.vertex_groups.clear()
vg_cog = body.vertex_groups.new(name="CenterBackCarFront")
vg_cog.add(list(range(len(body.data.vertices))), 1.0, 'REPLACE')

# Join body and smoothed wheels into single vehicle mesh
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
for w in smoothed_wheels:
    w.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
vh_mesh = bpy.context.view_layer.objects.active
vh_mesh.name = "cha_prowl_gs_deluxe2016_01"

# Ground wheels to Z = 0
min_z = min(v.co.z for v in vh_mesh.data.vertices)
for v in vh_mesh.data.vertices:
    v.co.z -= min_z
bm_fin = bmesh.new()
bm_fin.from_mesh(vh_mesh.data)
bmesh.ops.recalc_face_normals(bm_fin, faces=bm_fin.faces)
bm_fin.to_mesh(vh_mesh.data)
bm_fin.free()
vh_mesh.data.polygons.foreach_set("use_smooth", [True] * len(vh_mesh.data.polygons))
vh_mesh.data.use_auto_smooth = True
vh_mesh.data.auto_smooth_angle = 0.66
vh_mesh.data.update()

# Build vehicle armature with Prowl vehicle bones
arm_data = bpy.data.armatures.new("prowl_vehicle_arm")
vh_arm = bpy.data.objects.new("character_model", arm_data)
bpy.context.scene.collection.objects.link(vh_arm)
bpy.context.view_layer.objects.active = vh_arm
bpy.ops.object.mode_set(mode='EDIT')

for b in prowl_vh_bones:
    bn = b["name"]
    bx, by, bz = prowl_vh_bone_positions[bn]
    eb = arm_data.edit_bones.new(bn)
    eb.head = (bx, by, bz)
    eb.tail = (bx, by, bz + 0.15)

bpy.ops.object.mode_set(mode='OBJECT')

vh_mesh.parent = vh_arm
arm_mod = vh_mesh.modifiers.new(name="Armature", type='ARMATURE')
arm_mod.object = vh_arm
arm_mod.use_vertex_groups = True

# Export vehicle FBX WITHOUT bake_space_transform
bpy.ops.object.select_all(action='DESELECT')
vh_arm.select_set(True)
vh_mesh.select_set(True)
bpy.context.view_layer.objects.active = vh_arm

bpy.ops.export_scene.fbx(
    filepath=str(out_fbx_path),
    check_existing=False,
    use_selection=True,
    bake_anim=False,
    add_leaf_bones=False,
    apply_scale_options='FBX_SCALE_ALL',
    axis_forward='-Z',
    axis_up='Y'
)

print(f"\n[✓] Successfully exported Strongarm Vehicle prepared FBX to:\n  {out_fbx_path}")
