import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector, Matrix, Euler

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

armature = bpy.data.objects.get("brawl_ARM")
bpy.context.view_layer.objects.active = armature

# Let's inspect the world positions of the arm bones
for bname in ['bip_collar_L', 'bip_upperArm_L', 'bip_lowerArm_L', 'bip_hand_L',
              'bip_collar_R', 'bip_upperArm_R', 'bip_lowerArm_R', 'bip_hand_R']:
    pb = armature.pose.bones.get(bname)
    if pb:
        w_head = armature.matrix_world @ pb.head
        w_tail = armature.matrix_world @ pb.tail
        print(f"{bname:18s}: Head={w_head}, Tail={w_tail}")
