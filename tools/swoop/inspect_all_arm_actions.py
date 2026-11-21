import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

arm = bpy.data.objects.get("Bip001")

for act_name in ["dummy_attack_eye_L|transform_r|Base Layer", "dummy_attack_eye_L|awaken|Base Layer", "dummy_attack_eye_L|strengthen|Base Layer", "dummy_attack_eye_L|guard|Base Layer"]:
    act = bpy.data.actions.get(act_name)
    if act:
        print(f"Action {act.name}: frames {int(act.frame_range[0])} to {int(act.frame_range[1])}")

# Let's check Bip001 actions (the root armature actions)
for act in bpy.data.actions:
    if act.name.startswith("Bip001|"):
        print(f"  Armature action: {act.name}, frames: {int(act.frame_range[0])}-{int(act.frame_range[1])}")
