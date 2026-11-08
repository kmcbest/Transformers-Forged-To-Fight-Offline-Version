import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vortex_master.blend")
arm = bpy.data.objects["Vortex_ARM"]
print(f"Vortex_ARM rot: {arm.rotation_euler}, scale: {arm.scale}")

# Check key bone positions:
for bname in ["bip_pelvis", "bip_head", "bip_hand_L", "bip_hand_R", "bip_foot_L", "bip_foot_R"]:
    b = arm.data.bones.get(bname)
    if b:
        w_head = arm.matrix_world @ b.head_local
        print(f"  {bname:15s}: ({w_head.x:6.3f}, {w_head.y:6.3f}, {whead.z:6.3f})" if 'whead' in locals() else f"  {bname:15s}: ({w_head.x:6.3f}, {w_head.y:6.3f}, {w_head.z:6.3f})")
