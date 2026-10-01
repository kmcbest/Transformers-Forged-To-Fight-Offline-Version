# -*- coding: utf-8 -*-
"""
Phase 1: Scene Preparation for Hard Surface Grafting Pipeline.
Prepares demolishor_phase1.blend with:
- Ground Truth Ironhide 80-Bone Armature
- Ground Truth Ironhide Mesh (as semi-transparent reference silhouette)
- Source Demolishor FBX (Robot & Vehicle meshes + source armatures)
"""
import sys
import json
from pathlib import Path
import bpy
import mathutils
import math

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
DEMO_DIR = ROOT / "tools" / "demolishor"
SOURCE_FBX = ROOT / "3rd-party-models" / "transformers-fall-of-cybertron-demolishor" / "source" / "transformers fall of cybertron Demolishor.fbx"
BONES_JSON = DEMO_DIR / "ironhide_80_bones.json"
IRONHIDE_OBJ = DEMO_DIR / "ironhide_extracted" / "ironhide.obj"
OUTPUT_BLEND = DEMO_DIR / "demolishor_phase1.blend"

print("=== Setting up Phase 1 Blender Scene ===")
bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Build Reference 80-Bone Armature in Blender Space
# Unity coords: X=Right, Y=Up, Z=Forward
# Blender coords: X=Right, Y=Forward, Z=Up -> (x_u, z_u, y_u)
def unity_pos_to_blender(u_vec):
    return mathutils.Vector((u_vec[0], u_vec[2], u_vec[1]))

with open(BONES_JSON, "r", encoding="utf-8") as f:
    bones_data = json.load(f)

bone_order = bones_data["bone_order"]
bones_dict = bones_data["bones"]

arm_data = bpy.data.armatures.new("Ironhide_Reference_Armature")
arm_obj = bpy.data.objects.new("Ironhide_Reference_Armature", arm_data)
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
    eb.tail = b_head + mathutils.Vector((0, 0, 0.15))
    edit_bones[name] = eb

for name in bone_order:
    b_info = bones_dict[name]
    parent_name = b_info.get("parent")
    eb = edit_bones[name]
    if parent_name and parent_name in edit_bones:
        eb.parent = edit_bones[parent_name]
        p_eb = edit_bones[parent_name]
        diff = eb.head - p_eb.head
        if diff.length > 0.05:
            p_eb.tail = eb.head

bpy.ops.object.mode_set(mode='OBJECT')
arm_obj.show_in_front = True
print(f"[✓] Created Ironhide benchmark armature with {len(arm_obj.data.bones)} bones")

# 2. Import Ironhide Reference Mesh
if IRONHIDE_OBJ.exists():
    bpy.ops.wm.obj_import(filepath=str(IRONHIDE_OBJ))
    iron_obj = bpy.context.selected_objects[0] if bpy.context.selected_objects else bpy.data.objects.get("ironhide")
    if iron_obj:
        iron_obj.name = "Ironhide_Ghost_Reference"
        # Orient to match Blender coords (Unity obj was Y-up, in Blender obj_import usually maps -Z forward, Y up)
        # Convert coords so Z is Up and Y is Forward
        # Let's inspect its orientation:
        xs = [v.co.x for v in iron_obj.data.vertices]
        ys = [v.co.y for v in iron_obj.data.vertices]
        zs = [v.co.z for v in iron_obj.data.vertices]
        # In ironhide.obj: Y is height [0, 10.4], Z is depth [-1.6, 2.7]
        # In Blender world: height should be Z, depth should be Y
        for v in iron_obj.data.vertices:
            ox, oy, oz = v.co.x, v.co.y, v.co.z
            v.co.x = ox
            v.co.y = oz
            v.co.z = oy
        iron_obj.data.update()
        
        # Make transparent wireframe/ghost display
        iron_mat = bpy.data.materials.new(name="Ironhide_Ghost_Mat")
        iron_mat.use_nodes = True
        bsdf = iron_mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = (0.2, 0.6, 1.0, 1.0) # Light blue
            bsdf.inputs['Alpha'].default_value = 0.35
        iron_mat.blend_method = 'BLEND'
        iron_obj.data.materials.clear()
        iron_obj.data.materials.append(iron_mat)
        iron_obj.display_type = 'WIRE'
        print("[✓] Imported and aligned Ironhide ghost reference silhouette")

# 3. Create a Dedicated Collection for Demolishor Source
demo_col = bpy.data.collections.new("Demolishor_Source_FBX")
bpy.context.scene.collection.children.link(demo_col)

# Import Raw FBX
bpy.ops.import_scene.fbx(filepath=str(SOURCE_FBX))
imported = [o for o in bpy.context.selected_objects]

# Move imported objects to Demolishor collection
for o in imported:
    # Unlink from scene collection, link to demo_col
    if o.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(o)
    demo_col.objects.link(o)

print(f"[✓] Imported Demolishor FBX with {len(imported)} objects:")
for o in imported:
    print(f"    - {o.type}: {o.name}")

# Pre-align Demolishor robot mesh to match Ironhide coordinates
rb_mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
if rb_mesh:
    # Clear parent and modifiers from original FOC rig
    rb_mesh.parent = None
    rb_mesh.modifiers.clear()
    
    # Scale by 1.775 to reach 10.42m height, and rotate 90 deg around Z to face forward
    rb_mesh.scale = (1.775, 1.775, 1.775)
    rb_mesh.rotation_euler = (0, 0, math.radians(90))
    
    bpy.context.view_layer.objects.active = rb_mesh
    bpy.ops.object.select_all(action='DESELECT')
    rb_mesh.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    
    # Check bounds
    zs = [v.co.z for v in rb_mesh.data.vertices]
    min_z, max_z = min(zs), max(zs)
    print(f"[✓] Demolishor robot mesh pre-aligned: Z range [{min_z:.2f}, {max_z:.2f}] (Height: {max_z-min_z:.2f}m)")

# Focus 3D view on character
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'SOLID'
                space.shading.color_type = 'MATERIAL'

# Save to .blend file
OUTPUT_BLEND.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
print(f"\n[✓] Successfully saved Phase 1 scene to: {OUTPUT_BLEND}")
