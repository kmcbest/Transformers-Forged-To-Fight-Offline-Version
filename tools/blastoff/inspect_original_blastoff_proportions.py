import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm = bpy.data.objects['Blast-off_ARM']
for bname in ["bip_pelvis", "bip_spine_0", "bip_spine_1", "bip_neck", "bip_head", "C_Head01_Face_XF2"]:
    b = arm.data.bones.get(bname)
    if b:
        print(f"Original {bname:20s}: head={b.head_local}, length={b.length:.3f}")
