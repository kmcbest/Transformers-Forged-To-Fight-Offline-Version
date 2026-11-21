import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
from mathutils import Vector

ROOT = Path("e:/Agent/TFTF-blender")
FBX_SRC = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"
RAMJET_OBJ = ROOT / "toolchain/unity_build_project/Assets/Swoop/Ramjet/cha_ramjet_gs_deluxe2008_00.obj"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))
arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")

# 1. Check native idle01 & attack01 rotations on Clavicle01, Clavicle02, L Clavicle, L UpperArm
for act_name in ["Bip001|idle01|Base Layer", "Bip001|attack01|Base Layer", "Bip001|smash|Base Layer"]:
    act = bpy.data.actions.get(act_name)
    if not act: continue
    arm.animation_data.action = act
    bpy.context.scene.frame_set(5)
    bpy.context.view_layer.update()
    print(f"\n=== Native Action: {act_name} (frame 5) ===")
    for bn in ["Bip001 L Clavicle", "Bone_L_Clavicle01", "Bone_L_Clavicle02", "Bip001 L UpperArm", "Bone_L_UpperArm"]:
        pb = arm.pose.bones.get(bn)
        if pb:
            ang = pb.rotation_quaternion.to_euler('XYZ')
            deg = tuple(round(x * 57.2958, 1) for x in ang)
            print(f"  {bn:20s}: euler_deg={deg}")

# 2. Check why wings/beak detached in vehicle_idle01
act_v = bpy.data.actions.get("Bip001|vehicle_idle01|Base Layer")
arm.animation_data.action = act_v
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
print("\n=== Vehicle Idle01 (f1) Wing/Beak Location FCurves ===")
for fc in act_v.fcurves:
    if any(k in fc.data_path for k in ["Wing", "beak", "bird_Head"]) and "location" in fc.data_path:
        val = fc.evaluate(1)
        print(f"  {fc.data_path}[{fc.array_index}] = {val:.4f}")
for bn in ["Back", "Bone_L_Wing_01(mirrored)", "Bone_L_Wing_02(mirrored)", "bird_Head", "beak", "beak_the bottom"]:
    pb = arm.pose.bones.get(bn)
    if pb:
        print(f"  pb {bn:26s}: loc={tuple(round(x,4) for x in pb.location)}, scl={tuple(round(x,4) for x in pb.scale)}")
