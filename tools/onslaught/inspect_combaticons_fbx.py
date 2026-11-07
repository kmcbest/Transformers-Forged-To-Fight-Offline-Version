import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import os

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"

# Clear existing scene
bpy.ops.wm.read_factory_settings(use_empty=True)

print("Importing FBX...")
bpy.ops.import_scene.fbx(filepath=fbx_path)

print(f"Total objects in scene: {len(bpy.data.objects)}")
print(f"Total meshes in scene: {len(bpy.data.meshes)}")
print(f"Total materials: {len(bpy.data.materials)}")
print(f"Total armatures: {len(bpy.data.armatures)}")

print("\n--- Armatures ---")
for arm in bpy.data.armatures:
    print(f"Armature: {arm.name}, bones: {len(arm.bones)}")

print("\n--- Materials & Texture References ---")
for mat in bpy.data.materials:
    print(f"\nMaterial: {mat.name}")
    if mat.use_nodes and mat.node_tree:
        for node in mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE':
                image_name = node.image.name if node.image else "No Image"
                filepath = node.image.filepath if node.image else "No Path"
                print(f"  Image Node: {node.name}, Image: {image_name}, Path: {filepath}")
    else:
        print("  (No nodes)")

print("\n--- Objects & Meshes Summary ---")
obj_summary = []
for obj in bpy.data.objects:
    parent_name = obj.parent.name if obj.parent else "None"
    mat_names = [slot.material.name for slot in obj.material_slots if slot.material]
    obj_summary.append((obj.name, obj.type, parent_name, len(obj.data.vertices) if obj.type == 'MESH' else 0, mat_names))

# Print objects grouped or filtered
for name, otype, parent, vcount, mats in obj_summary:
    print(f"Object: {name} | Type: {otype} | Parent: {parent} | Verts: {vcount} | Mats: {mats}")
