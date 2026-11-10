import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import numpy as np

fbx_path = r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

orig_arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if orig_arm.animation_data:
    orig_arm.animation_data_clear()
orig_arm.data.pose_position = 'REST'
bpy.context.view_layer.update()

mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
for m in list(mesh_objs):
    if m.name in ["bot:mask_geo", "bot:faceMaskOn_jaw_geo"]:
        bpy.data.objects.remove(m, do_unlink=True)
        mesh_objs.remove(m)

for m in mesh_objs:
    bpy.ops.object.select_all(action='DESELECT')
    m.select_set(True)
    bpy.context.view_layer.objects.active = m
    for mod in list(m.modifiers):
        if mod.type == 'ARMATURE':
            bpy.ops.object.modifier_apply(modifier=mod.name)
    m.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

bpy.data.objects.remove(orig_arm, do_unlink=True)

# Calculate height before join
all_verts_y = [v.co.y for m in mesh_objs for v in m.data.vertices]
raw_height = max(all_verts_y) - min(all_verts_y)
scale_factor = 9.3040 / raw_height
min_y_ground = min(all_verts_y)
print(f"Raw height: {raw_height:.4f}, scale: {scale_factor:.4f}, min_y: {min_y_ground:.4f}")

# For submeshes of interest:
# Convert to Unity coords:
# In Blender raw FBX:
# Y is Up, X is Left/Right, Z is Forward/Back
# To match Prowl in Unity:
# Unity X = -X * scale_factor (mirror X)
# Unity Y = (Y - min_y_ground) * scale_factor (scale height)
# Unity Z = Z * scale_factor
parts = ["bot:palm_geo_L", "bot:palm_geo_R", "bot:arm_geo_L", "bot:arm_geo_R", "bot:shoulderBall_geo_L", "bot:face_geo"]
for p in parts:
    obj = bpy.data.objects.get(p)
    if obj:
        verts = np.array([v.co for v in obj.data.vertices])
        mean_v = np.mean(verts, axis=0)
        ux = -mean_v[0] * scale_factor
        uy = (mean_v[1] - min_y_ground) * scale_factor
        uz = mean_v[2] * scale_factor
        print(f"{p:25s}: Unity pos = ({ux:.3f}, {uy:.3f}, {uz:.3f})")
