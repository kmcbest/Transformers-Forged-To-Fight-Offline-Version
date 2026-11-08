import bpy
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Clear existing objects
bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
print(f"Loading FBX: {fbx_path}")
bpy.ops.import_scene.fbx(filepath=fbx_path)

print(f"\n--- Total Objects: {len(bpy.data.objects)} ---")
vortex_objs = []
all_objs_summary = {}

for obj in bpy.data.objects:
    otype = obj.type
    all_objs_summary[otype] = all_objs_summary.get(otype, 0) + 1
    name_lower = obj.name.lower()
    if "vortex" in name_lower or "heli" in name_lower or "rotor" in name_lower or "blade" in name_lower:
        vortex_objs.append(obj)

print("Object types summary:", all_objs_summary)
print(f"\nVortex related objects ({len(vortex_objs)}):")
for obj in vortex_objs:
    dim = obj.dimensions
    loc = obj.location
    parent_name = obj.parent.name if obj.parent else "None"
    mats = [m.name for m in obj.data.materials] if obj.type == 'MESH' and obj.data else []
    print(f"  [{obj.type:8s}] {obj.name:35s} | Parent: {parent_name:25s} | Dims: ({dim.x:.2f}, {dim.y:.2f}, {dim.z:.2f}) | Mats: {mats}")

print("\n--- All Meshes in Scene (filtering for any Combaticon names) ---")
combaticons = ["brawl", "swindle", "blastoff", "blast_off", "blast", "onslaught", "vortex", "bruticus", "wep", "vh", "rb"]
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        nl = obj.name.lower()
        matched = [c for c in combaticons if c in nl]
        if "vortex" in matched:
            continue # already listed
        if matched:
            pass # we know other bots are there

print("\n--- All Materials in Scene referencing 'vortex' ---")
for mat in bpy.data.materials:
    if "vortex" in mat.name.lower():
        print(f"  Material: {mat.name}")
        for slot in mat.node_tree.nodes if mat.use_nodes else []:
            if slot.type == 'TEX_IMAGE' and slot.image:
                print(f"    Image: {slot.image.name} ({slot.image.filepath})")
