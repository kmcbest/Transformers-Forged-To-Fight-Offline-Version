import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm_r = bpy.data.objects.get("RB_Swindle_CHARSKEL_ArmLoR.mo.dmx")
baz = bpy.data.objects.get("Bazooka_ARM.dmx")

print("ArmLoR mats:", [m.name for m in arm_r.data.materials if m])
print("Bazooka mats:", [m.name for m in baz.data.materials if m])

bb_arm = [arm_r.matrix_world @ v.co for v in arm_r.data.vertices]
bb_baz = [baz.matrix_world @ v.co for v in baz.data.vertices]

print(f"ArmLoR bounds: X=[{min(v.x for v in bb_arm):.2f}, {max(v.x for v in bb_arm):.2f}], Y=[{min(v.y for v in bb_arm):.2f}, {max(v.y for v in bb_arm):.2f}], Z=[{min(v.z for v in bb_arm):.2f}, {max(v.z for v in bb_arm):.2f}]")
print(f"Bazooka bounds: X=[{min(v.x for v in bb_baz):.2f}, {max(v.x for v in bb_baz):.2f}], Y=[{min(v.y for v in bb_baz):.2f}, {max(v.y for v in bb_baz):.2f}], Z=[{min(v.z for v in bb_baz):.2f}, {max(v.z for v in bb_baz):.2f}]")
