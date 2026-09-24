# -*- coding: utf-8 -*-
import bpy
import mathutils
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Import Ironhide OBJ
bpy.ops.wm.obj_import(filepath="tools/demolishor/ironhide_extracted/ironhide.obj")
iron_obj = bpy.data.objects["ironhide"]

# 2. Import Demolishor FBX
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

demo_mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
demo_arm = bpy.data.objects.get("Demolishor_ARM")

# Clean other objects
for o in list(bpy.data.objects):
    if o not in [iron_obj, demo_mesh, demo_arm]:
        bpy.data.objects.remove(o, do_unlink=True)

# Transform Demolishor mesh: X=-y*s, Y=z*s, Z=x*s
s = 1.778157
for v in demo_mesh.data.vertices:
    x_old, y_old, z_old = v.co.x, v.co.y, v.co.z
    v.co.x = -y_old * s
    v.co.y = z_old * s
    v.co.z = x_old * s

demo_mesh.data.update()

# Position side-by-side: Demolishor on Left (X=-5), Ironhide on Right (X=+5)
demo_mesh.location.x = -5.0
iron_obj.location.x = 5.0

# Set up Camera
cam_data = bpy.data.cameras.new("FrontCam")
cam_obj = bpy.data.objects.new("FrontCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# Camera position: front view
cam_obj.location = (0, -26, 5.2)
cam_obj.rotation_euler = (1.570796, 0, 0) # 90 deg around X

# Set up simple light
light_data = bpy.data.lights.new(name="Sun", type='SUN')
light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
bpy.context.scene.collection.objects.link(light_obj)
light_obj.location = (5, -20, 15)
light_obj.rotation_euler = (0.7, 0.2, 0.5)

# Render settings
bpy.context.scene.render.resolution_x = 1200
bpy.context.scene.render.resolution_y = 800
bpy.context.scene.render.image_settings.file_format = 'PNG'

out_img = Path("C:/Users/lenovo/.gemini/antigravity/brain/61450739-b3fd-40a5-b308-e6e69fbc5127/blender_side_by_side.png")
bpy.context.scene.render.filepath = str(out_img)
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered side-by-side to {out_img}")
