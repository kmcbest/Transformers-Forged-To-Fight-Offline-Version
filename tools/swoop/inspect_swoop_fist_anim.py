import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

fbx_src = Path(r"E:\Agent\TFTF-blender\3rd-party-models\swoop\01_master\Swoop_pbr.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_src))

arm = bpy.data.objects.get("Bip001")
print("Actions in Swoop_pbr.fbx:")
for act in bpy.data.actions:
    print(" ", act.name)

# Check finger rotations in idle01
act_idle = bpy.data.actions.get("Bip001|idle01|Base Layer")
if act_idle:
    arm.animation_data.action = act_idle
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    print("\nIn idle01 frame 1:")
    for pb in arm.pose.bones:
        if "finger" in pb.name.lower() or "hand" in pb.name.lower():
            print(f"  {pb.name}: rot={pb.rotation_quaternion or pb.rotation_euler}")
