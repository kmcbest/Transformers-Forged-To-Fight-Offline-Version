import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

cap_l = bpy.data.objects.get("RB_Brawl_CHARSKEL_CapL.mo.dmx")
arm_l = bpy.data.objects.get("RB_Brawl_CHARSKEL_ArmLoL.mo.dmx")

scene_y = bpy.data.objects.get("brawl_ARM").matrix_world.translation.y

print("CapL raw bounds (relative to scene Y):")
ys = [v.co.y - scene_y for v in cap_l.data.vertices]
zs = [v.co.z for v in cap_l.data.vertices]
print(f"  Y: [{min(ys):.3f}, {max(ys):.3f}], Z: [{min(zs):.3f}, {max(zs):.3f}]")

print("ArmLoL raw bounds (relative to scene Y):")
ys_a = [v.co.y - scene_y for v in arm_l.data.vertices]
zs_a = [v.co.z for v in arm_l.data.vertices]
print(f"  Y: [{min(ys_a):.3f}, {max(ys_a):.3f}], Z: [{min(zs_a):.3f}, {max(zs_a):.3f}]")
