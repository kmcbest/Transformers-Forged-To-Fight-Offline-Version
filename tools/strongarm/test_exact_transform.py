import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")

face = bpy.data.objects["bot:face_geo"]
arm_l = bpy.data.objects["bot:arm_geo_L"]
arm_r = bpy.data.objects["bot:arm_geo_R"]

# Test transform on face and arms:
# Step 1: rotate 90 deg around X
# Step 2: scale by (-1, -1, 1)
# Result:
# X_final = -X_maya
# Y_final = +Z_maya (Face was Z > 0, so Y_final > 0!)
# Z_final = +Y_maya (Head was Y > 0, so Z_final > 0!)

print(f"Face in raw FBX:  Z={face.data.vertices[0].co.z:.4f}")
print(f"Arm_L in raw FBX: X={arm_l.data.vertices[0].co.x:.4f} (Blue Siren)")
print(f"Arm_R in raw FBX: X={arm_r.data.vertices[0].co.x:.4f} (Red Siren)")

print(f"\nAfter (-X, +Z, +Y) mapping:")
print(f"Face Y:  {face.data.vertices[0].co.z:.4f} (Positive = Facing Forward!)")
print(f"Arm_L X: {-arm_l.data.vertices[0].co.x:.4f} (Negative = Left side!)")
print(f"Arm_R X: {-arm_r.data.vertices[0].co.x:.4f} (Positive = Right side!)")
