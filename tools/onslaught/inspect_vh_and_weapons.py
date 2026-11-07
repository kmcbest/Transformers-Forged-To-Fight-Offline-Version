import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

print("=== CHECKING ONSLAUGHT_VH_ARM AND VH.DMX ===")
vh_obj = bpy.data.objects.get("VH.dmx")
vh_arm = bpy.data.objects.get("Onslaught_VH_ARM")

if vh_obj:
    print(f"VH.dmx: type={vh_obj.type}, parent={vh_obj.parent}, loc={vh_obj.matrix_world.translation}")
    print(f"Modifiers: {[m.name + ' (' + m.type + ')' for m in vh_obj.modifiers]}")
    for m in vh_obj.modifiers:
        if m.type == 'ARMATURE':
            print(f"  Armature modifier target: {m.object}")

if vh_arm:
    print(f"Onslaught_VH_ARM: loc={vh_arm.matrix_world.translation}, rot={vh_arm.rotation_euler}, scale={vh_arm.scale}")
    print(f"Bones count: {len(vh_arm.data.bones)}")
    # Check some bone names
    bnames = [b.name for b in vh_arm.data.bones]
    print(f"Sample bone names: {bnames[:15]}")

print("\n=== CHECKING WEAPON OBJECTS ===")
for obj in bpy.data.objects:
    if "rocket" in obj.name.lower() or "launcher" in obj.name.lower():
        print(f"Object: {obj.name}, type={obj.type}, parent={obj.parent}, loc={obj.matrix_world.translation}")
        print(f"Modifiers: {[m.name + ' (' + m.type + ')' for m in obj.modifiers]}")
        for m in obj.modifiers:
            if m.type == 'ARMATURE':
                print(f"  Armature modifier target: {m.object}")

print("\n=== ARE THERE OTHER WEAPONS IN THE FBX? ===")
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        mats = [s.material.name for s in obj.material_slots if s.material]
        has_wep_mat = any("wep" in m.lower() for m in mats)
        if has_wep_mat or "wep" in obj.name.lower():
            print(f"Mesh: {obj.name}, Parent={obj.parent.name if obj.parent else 'None'}, Mats={mats}, Loc={obj.matrix_world.translation}")
