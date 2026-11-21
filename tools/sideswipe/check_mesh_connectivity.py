import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy

ROBOT_FBX = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=ROBOT_FBX)

# Check distance between Bip_UpperArm_L bone head and the shoulder vertices
m_torso = bpy.data.objects.get("48")
m_arms = bpy.data.objects.get("48.001")
m_sw_r = bpy.data.objects.get("44.002")

print("Checking objects in scene:")
for o in [m_torso, m_arms, m_sw_r]:
    if o:
        print(f"Object {o.name}: loc={o.location}, rot={o.rotation_euler}, scale={o.scale}")
        xs = [(o.matrix_world @ v.co).x for v in o.data.vertices]
        ys = [(o.matrix_world @ v.co).y for v in o.data.vertices]
        zs = [(o.matrix_world @ v.co).z for v in o.data.vertices]
        print(f"  Bounds: X=[{min(xs):.4f}, {max(xs):.4f}], Y=[{min(ys):.4f}, {max(ys):.4f}], Z=[{min(zs):.4f}, {max(zs):.4f}]")
