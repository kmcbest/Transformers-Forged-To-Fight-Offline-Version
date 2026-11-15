import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

blend_path = r'E:\Agent\TFTF-blender\3rd-party-models\blitzwing_extracted\rar\Blitzwing.blend'
bpy.ops.wm.open_mainfile(filepath=blend_path)

arm = bpy.data.objects['Blitzwing_Skeleton']
print("Blitzwing_Skeleton bones:")
for bname in ['bip_upperArm_L', 'bip_upperArm_R', 'Bip01_L_Hand', 'Bip01_R_Hand']:
    if bname in arm.data.bones:
        b = arm.data.bones[bname]
        print(f"  {bname}: head={b.head}")
