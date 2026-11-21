import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy

FBX_SRC = Path("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/Swoop_pbr.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))
arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")

# Check frame 1 vs rest pose transforms of Wing_01, Wing_02, Back, bird_Head, beak, beak_the bottom
act_v = bpy.data.actions.get("Bip001|vehicle_idle01|Base Layer")
arm.animation_data.action = act_v
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()

print("=== Bone matrices in Bip001|vehicle_idle01 frame 1 ===")
for bn in ["Bip001", "Bip001 Spine1", "Back", "Bone_L_Wing_01(mirrored)", "Bone_L_Wing_02(mirrored)", "bird_chest", "bird_neck", "bird_Head", "beak", "beak_the bottom"]:
    pb = arm.pose.bones.get(bn)
    b = arm.data.bones.get(bn)
    if pb and b:
        # Compare pb.matrix vs b.matrix_local
        print(f"  {bn:26s}: head_rest={tuple(round(x,3) for x in b.head_local)} -> head_pose={tuple(round(x,3) for x in pb.head)}, pb.scale={tuple(round(x,3) for x in pb.scale)}")
