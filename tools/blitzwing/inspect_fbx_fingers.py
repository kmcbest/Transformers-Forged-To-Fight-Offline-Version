import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

# Let's inspect BlitzwingHandFixer.cs logic
# Why did bone remap table map bones, and what were the bone weights?
# Let's write a test script that inspects blitzwing_robot.fbx in Unity or Blender.

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = r'E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\blitzwing_robot.fbx'
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
arm = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE'][0]

print(f"FBX Mesh: {mesh.name}, verts={len(mesh.data.vertices)}")
print(f"FBX Armature: {arm.name}, bones={len(arm.data.bones)}")

# Check vertex group assignments for finger bones
for side in ['Left', 'Right']:
    hand_vg = mesh.vertex_groups.get(f'{side}Hand')
    print(f"\n--- {side} Hand Bones ---")
    if hand_vg:
        count = sum(1 for v in mesh.data.vertices for g in v.groups if g.group == hand_vg.index and g.weight > 0.01)
        print(f"  {side}Hand verts: {count}")
    for fi in ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']:
        for k in [1, 2, 3]:
            bname = f'{side}Hand{fi}{k}'
            vg = mesh.vertex_groups.get(bname)
            if vg:
                v_count = sum(1 for v in mesh.data.vertices for g in v.groups if g.group == vg.index and g.weight > 0.01)
                print(f"  {bname}: verts={v_count}")
            else:
                print(f"  {bname}: MISSING VG!")
