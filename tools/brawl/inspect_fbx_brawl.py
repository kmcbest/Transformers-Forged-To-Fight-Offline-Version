import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

# Clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
print(f"Loading FBX: {fbx_path}")
bpy.ops.import_scene.fbx(filepath=fbx_path)

armature = bpy.data.objects.get("brawl_ARM")
if armature:
    print(f"Found armature: {armature.name}, bones count: {len(armature.data.bones)}")
    bone_names = [b.name for b in armature.data.bones]
    print("Bones:", bone_names[:30])
    print("... total bones:", len(bone_names))
    for b in armature.data.bones:
        if "hand" in b.name.lower() or "finger" in b.name.lower() or "thumb" in b.name.lower():
            print(f"  Hand bone: {b.name}")
else:
    print("brawl_ARM not found!")

# Check meshes under brawl
brawl_meshes = [obj for obj in bpy.data.objects if "Brawl" in obj.name or "brawl" in obj.name]
print(f"Found {len(brawl_meshes)} objects with 'Brawl' in name:")
for obj in brawl_meshes:
    print(f"  {obj.type} : {obj.name} (parent={obj.parent.name if obj.parent else None})")
    if obj.type == 'MESH':
        print(f"    verts={len(obj.data.vertices)}, vgroups={len(obj.vertex_groups)}")
