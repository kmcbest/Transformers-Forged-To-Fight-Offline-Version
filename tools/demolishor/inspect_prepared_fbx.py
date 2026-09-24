# -*- coding: utf-8 -*-
import bpy
import mathutils
import sys

sys.stdout.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"d:\Agent\tftf\toolchain\unity_build_project\Assets\Demolishor\demolishor_prepared.fbx")

print("Objects in demolishor_prepared.fbx:")
for obj in bpy.data.objects:
    print(f"  {obj.name} (type: {obj.type})")
    if obj.type == 'MESH':
        xs = [v[0] for v in obj.bound_box]
        ys = [v[1] for v in obj.bound_box]
        zs = [v[2] for v in obj.bound_box]
        print(f"    X: [{min(xs):.2f}, {max(xs):.2f}]")
        print(f"    Y: [{min(ys):.2f}, {max(ys):.2f}]")
        print(f"    Z: [{min(zs):.2f}, {max(zs):.2f}]")
    elif obj.type == 'ARMATURE':
        print(f"    Bones count: {len(obj.data.bones)}")
        for b_name in ['Hips', 'Spine', 'Head', 'LeftArm', 'RightArm']:
            b = obj.data.bones.get(b_name)
            if b:
                print(f"    Bone {b_name}: head=({b.head_local[0]:.2f}, {b.head_local[1]:.2f}, {b.head_local[2]:.2f})")
