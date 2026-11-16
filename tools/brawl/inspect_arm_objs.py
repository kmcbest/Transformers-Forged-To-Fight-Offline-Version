import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm = bpy.data.objects.get("brawl_ARM")
test_bones = [
    'L_CloudA_PadRobo01_XT', 'L_CloudA_ShoulderRobo01_XT', 'L_CloudA_ElbowRobo01_XT',
    'R_CloudA_PadRobo01_XT', 'R_CloudA_ShoulderRobo01_XT', 'R_CloudA_ElbowRobo01_XT'
]

for bn in test_bones:
    b = arm.data.bones.get(bn)
    if b:
        chain = []
        c = b
        while c:
            chain.append(c.name)
            c = c.parent
        print(f"Bone {bn} -> {' -> '.join(chain)}")
    else:
        print(f"Bone {bn} NOT FOUND in armature!")
