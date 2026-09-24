# -*- coding: utf-8 -*-
import bpy
import mathutils
import sys

sys.stdout.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Import Ironhide OBJ
bpy.ops.wm.obj_import(filepath="tools/demolishor/ironhide_extracted/ironhide.obj")
iron_obj = bpy.data.objects["ironhide"]

# 2. Import Demolishor FBX
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

demo_mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")

# Transform Demolishor mesh vertices directly:
# X_new = -Y_old * 1.778157
# Y_new = Z_old * 1.778157
# Z_new = X_old * 1.778157
s = 1.778157
for v in demo_mesh.data.vertices:
    x_old, y_old, z_old = v.co.x, v.co.y, v.co.z
    v.co.x = -y_old * s
    v.co.y = z_old * s
    v.co.z = x_old * s

demo_mesh.data.update()

xs_i = [v.co.x for v in iron_obj.data.vertices]
ys_i = [v.co.y for v in iron_obj.data.vertices]
zs_i = [v.co.z for v in iron_obj.data.vertices]

xs_d = [v.co.x for v in demo_mesh.data.vertices]
ys_d = [v.co.y for v in demo_mesh.data.vertices]
zs_d = [v.co.z for v in demo_mesh.data.vertices]

print(f"\nIronhide:   X=[{min(xs_i):6.2f}, {max(xs_i):6.2f}]  Y=[{min(ys_i):6.2f}, {max(ys_i):6.2f}]  Z=[{min(zs_i):6.2f}, {max(zs_i):6.2f}]")
print(f"Demolishor: X=[{min(xs_d):6.2f}, {max(xs_d):6.2f}]  Y=[{min(ys_d):6.2f}, {max(ys_d):6.2f}]  Z=[{min(zs_d):6.2f}, {max(zs_d):6.2f}]")
