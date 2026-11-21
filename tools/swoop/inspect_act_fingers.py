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

for act_name in ["Bip001|idle01|Base Layer", "Bip001|attack01|Base Layer"]:
    act = bpy.data.actions.get(act_name)
    if not act: continue
    print(f"\n=== Action: {act_name} ===")
    arm.animation_data_create()
    arm.animation_data.action = act
    for f in [0, 10]:
        bpy.context.scene.frame_set(f)
        print(f"--- Frame {f} ---")
        for side in ["L", "R"]:
            f1 = arm.pose.bones[f"Bone_{side}_Finger1"].rotation_quaternion
            f2 = arm.pose.bones[f"Bone_{side}_Finger2"].rotation_quaternion
            f0 = arm.pose.bones[f"Bone_{side}_Finger0"].rotation_quaternion
            print(f"  {side} F1: ({f1.w:.3f}, {f1.x:.3f}, {f1.y:.3f}, {f1.z:.3f}), F2: ({f2.w:.3f}, {f2.x:.3f}, {f2.y:.3f}, {f2.z:.3f}), F0: ({f0.w:.3f}, {f0.x:.3f}, {f0.y:.3f}, {f0.z:.3f})")
