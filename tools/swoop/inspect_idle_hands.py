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
swoop_mesh = bpy.data.objects.get("Swoop.001")

# Clean scene
for o in list(bpy.data.objects):
    if o.name in ["Symbol_DC", "Shadow", "Swoop_Weapon", "Symbol_AB"]:
        bpy.data.objects.remove(o, do_unlink=True)

# Apply idle01 action to see how the hands look
act = bpy.data.actions.get("Bip001|idle01|Base Layer")
if act:
    arm.animation_data.action = act
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

# Let's inspect the position and rotation of Bone_L_Hand, Bone_R_Hand and fingers
for bname in ["Bone_L_Hand", "Bone_L_Finger0", "Bone_L_Finger1", "Bone_L_Finger2",
              "Bone_R_Hand", "Bone_R_Finger0", "Bone_R_Finger1", "Bone_R_Finger2"]:
    pb = arm.pose.bones.get(bname)
    if pb:
        print(f"{bname}: head={pb.head}, rot_euler={[round(x, 2) for x in pb.rotation_euler]}")
