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

arm = bpy.data.objects.get("Armature")
if arm:
    print(f"Armature scale: {arm.scale}, rot: {arm.rotation_euler}")
    for b in arm.data.bones:
        h = arm.matrix_world @ b.head_local
        t = arm.matrix_world @ b.tail_local
        print(f"  {b.name:20s}: head=({h.x:7.4f}, {h.y:7.4f}, {h.z:7.4f}) tail=({t.x:7.4f}, {t.y:7.4f}, {t.z:7.4f})")
