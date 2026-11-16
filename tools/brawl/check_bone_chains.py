import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

armature = bpy.data.objects.get("brawl_ARM")

bones_to_check = [
    'L_CloudA_ShoulderRobo01_XT', 'L_CloudA_ShoulderRobo02_XT', 'L_CloudA_ShoulderRobo03_XT',
    'L_CloudA_PadRobo01_XT', 'L_CloudA_PadRobo02_XT', 'L_CloudA_PadRobo03_XT',
    'L_CloudA_ElbowRobo01_XT', 'L_CloudA_ElbowRobo02_XT', 'bip_hand_L',
    'bip_collar_L', 'bip_upperArm_L', 'bip_lowerArm_L'
]

for bname in bones_to_check:
    b = armature.data.bones.get(bname)
    if b:
        chain = []
        curr = b
        while curr:
            chain.append(curr.name)
            curr = curr.parent
        print(f"{bname:30s} -> {' -> '.join(chain[:5])}")
