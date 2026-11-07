import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\onslaught\onslaught_master.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))

print("=== CHECKING TEXTURES IN MASTER BLEND ===")
missing_images = 0
total_images = 0

for img in bpy.data.images:
    total_images += 1
    p = Path(bpy.path.abspath(img.filepath))
    exists = p.exists()
    status = "[OK]" if exists else "[MISSING]"
    if not exists:
        missing_images += 1
    print(f"{status} Image: {img.name} -> Path: {p} (exists: {exists})")

print(f"\nTotal images: {total_images}, Missing: {missing_images}")

# Setup camera and lighting to render preview images
def setup_render_scene():
    # Remove existing cameras and lights
    for obj in list(bpy.data.objects):
        if obj.type in ['CAMERA', 'LIGHT']:
            bpy.data.objects.remove(obj, do_unlink=True)
            
    # Add sun light
    light_data = bpy.data.lights.new(name="Sun", type='SUN')
    light_data.energy = 4.0
    light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
    bpy.context.scene.collection.objects.link(light_obj)
    light_obj.rotation_euler = (0.785, 0.3, 0.6)
    
    # Add fill light
    light_data2 = bpy.data.lights.new(name="FillSun", type='SUN')
    light_data2.energy = 2.0
    light_obj2 = bpy.data.objects.new(name="FillSun", object_data=light_data2)
    bpy.context.scene.collection.objects.link(light_obj2)
    light_obj2.rotation_euler = (-0.785, -0.3, -2.5)

    # Add camera
    cam_data = bpy.data.cameras.new(name="Cam")
    cam_obj = bpy.data.objects.new(name="Cam", object_data=cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    
    # Configure render settings
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.resolution_x = 960
    bpy.context.scene.render.resolution_y = 720
    return cam_obj

# 1. Render Robot Front
cam = setup_render_scene()
# In FOC, robot is Z-up, front faces +X (or let's check bounding center)
# Let's hide Vehicle and Weapons collections
coll_robot = bpy.data.collections.get("01_Onslaught_Robot")
coll_weapons = bpy.data.collections.get("02_Onslaught_Weapons")
coll_vh = bpy.data.collections.get("03_Onslaught_Vehicle")

if coll_vh:
    coll_vh.hide_render = True
if coll_weapons:
    coll_weapons.hide_render = False # show with back rocket launchers

# Position camera for Robot Front (looking at origin around Z=2.8)
# Robot height is ~5.5m, Z is [0, 5.5], X is front/back
# Let's inspect robot bounds
robot_mesh = bpy.data.objects.get("RB_Onslaught_CHARSKEL_Chest.mo.dmx")

cam.location = (8.0, -3.0, 3.2)
cam.rotation_euler = (1.4, 0.0, 1.95)

out_robot = str(blend_path.parent / "preview_onslaught_robot.png")
bpy.context.scene.render.filepath = out_robot
bpy.ops.render.render(write_still=True)
print(f"[OK] Rendered robot preview: {out_robot}")

# 2. Render Vehicle
if coll_robot:
    coll_robot.hide_render = True
if coll_weapons:
    coll_weapons.hide_render = True
if coll_vh:
    coll_vh.hide_render = False

cam.location = (7.0, -5.0, 3.5)
cam.rotation_euler = (1.2, 0.0, 0.95)

out_vh = str(blend_path.parent / "preview_onslaught_vehicle.png")
bpy.context.scene.render.filepath = out_vh
bpy.ops.render.render(write_still=True)
print(f"[OK] Rendered vehicle preview: {out_vh}")
