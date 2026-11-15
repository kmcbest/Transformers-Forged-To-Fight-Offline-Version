import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

blend_path = r'E:\Agent\TFTF-blender\3rd-party-models\blitzwing_extracted\rar\Blitzwing.blend'
bpy.ops.wm.open_mainfile(filepath=blend_path)
arm = bpy.data.objects['Blitzwing_Skeleton']

bones_to_measure = [
    'bip_pelvis', 'bip_spine_0', 'bip_spine_1', 'bip_spine_2', 'bip_neck', 'bip_head',
    'bip_collar_L', 'bip_upperArm_L', 'bip_lowerArm_L', 'Bip01_L_Hand',
    'bip_hip_L', 'bip_knee_L', 'bip_foot_L', 'bip_toe_L'
]

print("=== Blitzwing Bone Dimensions ===")
for bname in bones_to_measure:
    b = arm.data.bones.get(bname)
    if b:
        hl = arm.matrix_world @ b.head_local
        tl = arm.matrix_world @ b.tail_local
        print(f"  {bname:15s}: head=({hl.x:.3f}, {hl.y:.3f}, {hl.z:.3f}), length={(tl-hl).length:.3f}")
