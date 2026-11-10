import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

fbx_path = Path(r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
print(f"Armatures: {len(arms)}, Meshes: {len(meshes)}")
if arms:
    arm = arms[0]
    print(f"Armature name: {arm.name}, bones: {len(arm.data.bones)}")
    print(f"Animation data: {arm.animation_data}")
    if arm.animation_data and arm.animation_data.action:
        print(f"Action: {arm.animation_data.action.name}, frames: {arm.animation_data.action.frame_range}")
    # Check if meshes have armature modifiers
    for m in meshes[:5]:
        mods = [mod.type for mod in m.modifiers]
        print(f"Mesh: {m.name}, parent: {m.parent.name if m.parent else None}, mods: {mods}")
