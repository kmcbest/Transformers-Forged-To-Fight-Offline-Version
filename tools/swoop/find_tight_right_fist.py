import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

FBX_SRC = Path("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

arm = bpy.data.objects.get("Bip001")

for act in bpy.data.actions:
    if not act.name.startswith("Bip001|"): continue
    arm.animation_data_create()
    arm.animation_data.action = act
    # Check max Z curl of Bone_R_Finger1 and Bone_R_Finger2
    for f in range(min(5, int(act.frame_range[1]))):
        bpy.context.scene.frame_set(f)
        rf1 = arm.pose.bones["Bone_R_Finger1"].rotation_quaternion
        rf2 = arm.pose.bones["Bone_R_Finger2"].rotation_quaternion
        if abs(rf1.z) > 0.3 or abs(rf2.z) > 0.4:
            print(f"Action {act.name} f{f}: R_F1 z={rf1.z:.3f}, R_F2 z={rf2.z:.3f}")
            break
