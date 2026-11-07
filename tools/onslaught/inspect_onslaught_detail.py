import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

print("=== ALL OBJECTS WITH 'Onslaught' OR 'Rocket' OR 'VH' OR 'WEP' ===")
for obj in bpy.data.objects:
    name_lower = obj.name.lower()
    mat_names = [slot.material.name for slot in obj.material_slots if slot.material]
    parent = obj.parent.name if obj.parent else "None"
    
    # Check if related to Onslaught, weapons, or vehicles
    is_related = False
    if "onslaught" in name_lower or "rocket" in name_lower or "wep" in name_lower:
        is_related = True
    elif "vh" in name_lower and not ("blast" in name_lower or "brawl" in name_lower or "vortex" in name_lower or "swindle" in name_lower):
        is_related = True
    for m in mat_names:
        if "onslaught" in m.lower():
            is_related = True
            
    if is_related:
        print(f"[{obj.type}] {obj.name} | Parent: {parent} | Mats: {mat_names}")
        if obj.type == 'MESH':
            verts = len(obj.data.vertices)
            dims = obj.dimensions
            loc = obj.matrix_world.translation
            print(f"   Verts: {verts}, Dims: ({dims.x:.2f}, {dims.y:.2f}, {dims.z:.2f}), Loc: ({loc.x:.2f}, {loc.y:.2f}, {loc.z:.2f})")
            # print vertex group names
            vg_names = [vg.name for vg in obj.vertex_groups]
            if vg_names:
                print(f"   Vertex groups count: {len(vg_names)}, first 5: {vg_names[:5]}")
        elif obj.type == 'ARMATURE':
            bones = [b.name for b in obj.data.bones]
            print(f"   Bones count: {len(bones)}, root bones: {[b.name for b in obj.data.bones if not b.parent]}")

print("\n=== ALL WEAPONS IN SCENE ===")
for obj in bpy.data.objects:
    if "wep" in obj.name.lower() or "rocket" in obj.name.lower():
        print(f"Weapon: {obj.name} | Type: {obj.type} | Parent: {obj.parent.name if obj.parent else 'None'}")
        if obj.type == 'MESH':
            print(f"   Dims: {obj.dimensions}, Loc: {obj.matrix_world.translation}")
