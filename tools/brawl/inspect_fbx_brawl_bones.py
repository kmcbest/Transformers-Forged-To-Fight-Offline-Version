import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

armature = bpy.data.objects.get("brawl_ARM")
if armature:
    print("\n--- BRAWL_ARM BONES ---")
    for b in armature.data.bones:
        if b.name.startswith("bip_") or "head" in b.name.lower() or "neck" in b.name.lower() or "root" in b.name.lower() or "cannon" in b.name.lower():
            print(f"  {b.name} (parent: {b.parent.name if b.parent else None})")

print("\n--- VEHICLE ARM ---")
vh_arm = bpy.data.objects.get("brawl_VH_ARM")
if vh_arm:
    print(f"brawl_VH_ARM bones count: {len(vh_arm.data.bones)}")
    for b in list(vh_arm.data.bones)[:20]:
        print(f"  {b.name}")

vh_mesh = bpy.data.objects.get("VH_BrawlCINE_SKEL.001.dmx")
if vh_mesh:
    print(f"VH Mesh parent: {vh_mesh.parent.name if vh_mesh.parent else None}")
    print(f"VH Mesh bounds: {vh_mesh.dimensions}")
