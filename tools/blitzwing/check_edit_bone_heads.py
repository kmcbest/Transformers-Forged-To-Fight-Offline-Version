import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

blend_path = r'E:\Agent\TFTF-blender\3rd-party-models\blitzwing_extracted\rar\Blitzwing.blend'
bpy.ops.wm.open_mainfile(filepath=blend_path)
arm = bpy.data.objects['Blitzwing_Skeleton']
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')

for bname in ['bip_hip_L', 'bip_knee_L', 'bip_foot_L', 'bip_toe_L']:
    eb = arm.data.edit_bones[bname]
    print(f"EditBone {bname:12s}: head={eb.head}, tail={eb.tail}")
