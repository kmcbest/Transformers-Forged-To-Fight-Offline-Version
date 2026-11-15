import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

blend_path = r'E:\Agent\TFTF-blender\3rd-party-models\blitzwing_extracted\rar\Blitzwing.blend'
bpy.ops.wm.open_mainfile(filepath=blend_path)
mesh = bpy.data.objects['Blitzwing']
arm = bpy.data.objects['Blitzwing_Skeleton']

min_z = min(v.co.z for v in mesh.data.vertices)
foot_bone = arm.data.bones['bip_foot_L']
knee_bone = arm.data.bones['bip_knee_L']
toe_bone = arm.data.bones['bip_toe_L']

print(f"Knee bone head: {knee_bone.head}, tail: {knee_bone.tail}")
print(f"Foot bone head: {foot_bone.head}, tail: {foot_bone.tail}")
print(f"Toe bone head:  {toe_bone.head}, tail: {toe_bone.tail}")
