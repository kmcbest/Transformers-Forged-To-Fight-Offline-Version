import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\onslaught\onslaught_master.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))

# Remove cameras and lights
for obj in list(bpy.data.objects):
    if obj.type in ['CAMERA', 'LIGHT']:
        bpy.data.objects.remove(obj, do_unlink=True)
        
# Add lights
light_data = bpy.data.lights.new(name="Sun", type='SUN')
light_data.energy = 4.0
light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
bpy.context.scene.collection.objects.link(light_obj)
light_obj.rotation_euler = (0.785, 0.3, 0.6)

light_data2 = bpy.data.lights.new(name="FillSun", type='SUN')
light_data2.energy = 2.0
light_obj2 = bpy.data.objects.new(name="FillSun", object_data=light_data2)
bpy.context.scene.collection.objects.link(light_obj2)
light_obj2.rotation_euler = (-0.785, -0.3, -2.5)

cam_data = bpy.data.cameras.new(name="Cam")
cam_obj = bpy.data.objects.new(name="Cam", object_data=cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 960
bpy.context.scene.render.resolution_y = 720

# Hide robot and vehicle, show only weapons
coll_robot = bpy.data.collections.get("01_Onslaught_Robot")
coll_weapons = bpy.data.collections.get("02_Onslaught_Weapons")
coll_vh = bpy.data.collections.get("03_Onslaught_Vehicle")

if coll_robot:
    coll_robot.hide_render = True
if coll_vh:
    coll_vh.hide_render = True
if coll_weapons:
    coll_weapons.hide_render = False

cam_obj.location = (6.0, -4.0, 3.5)
cam_obj.rotation_euler = (1.3, 0.0, 1.1)

out_wpn = str(blend_path.parent / "preview_onslaught_weapons.png")
bpy.context.scene.render.filepath = out_wpn
bpy.ops.render.render(write_still=True)
print(f"[OK] Rendered weapons preview: {out_wpn}")
