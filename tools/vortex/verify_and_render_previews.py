import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
from pathlib import Path

TARGET_ROOT = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex")
ROBOT_BLEND = TARGET_ROOT / "robot" / "vortex_robot.blend"
VH_BLEND = TARGET_ROOT / "vehicle" / "vortex_vehicle.blend"
WPN_BLEND = TARGET_ROOT / "weapons" / "vortex_weapons.blend"

def setup_studio_lighting_and_cam(cam_loc, cam_rot, cam_lens=50):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.use_bloom = True
    scene.eevee.use_gtao = True
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    
    # World background dark gray
    world = bpy.data.worlds.new("StudioWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.04, 0.04, 0.05, 1.0)
        bg.inputs["Strength"].default_value = 1.0
    scene.world = world
    
    # Sun key light
    sun_data = bpy.data.lights.new(name="SunKey", type='SUN')
    sun_data.energy = 3.5
    sun_data.color = (1.0, 0.98, 0.95)
    sun_obj = bpy.data.objects.new(name="SunKey", object_data=sun_data)
    sun_obj.rotation_euler = (math.radians(50), math.radians(20), math.radians(-35))
    bpy.context.collection.objects.link(sun_obj)
    
    # Fill light
    fill_data = bpy.data.lights.new(name="FillLight", type='POINT')
    fill_data.energy = 500
    fill_data.color = (0.7, 0.85, 1.0)
    fill_obj = bpy.data.objects.new(name="FillLight", object_data=fill_data)
    fill_obj.location = (-4, -4, 4)
    bpy.context.collection.objects.link(fill_obj)
    
    # Camera
    cam_data = bpy.data.cameras.new(name="StudioCam")
    cam_data.lens = cam_lens
    cam_obj = bpy.data.objects.new(name="StudioCam", object_data=cam_data)
    cam_obj.location = cam_loc
    cam_obj.rotation_euler = [math.radians(a) for a in cam_rot]
    bpy.context.collection.objects.link(cam_obj)
    scene.camera = cam_obj

# 1. Render Robot Preview
print("\n--- Rendering Robot Preview ---")
bpy.ops.wm.open_mainfile(filepath=str(ROBOT_BLEND))
setup_studio_lighting_and_cam(cam_loc=(0, -8.5, 3.2), cam_rot=(85, 0, 0), cam_lens=45)
out_robot = TARGET_ROOT / "preview_vortex_robot.png"
bpy.context.scene.render.filepath = str(out_robot)
bpy.ops.render.render(write_still=True)
print(f"[OK] Rendered {out_robot}")

# 2. Render Vehicle Preview
print("\n--- Rendering Vehicle Preview ---")
bpy.ops.wm.open_mainfile(filepath=str(VH_BLEND))
setup_studio_lighting_and_cam(cam_loc=(7.0, -11.0, 6.0), cam_rot=(65, 0, 32), cam_lens=40)
out_vh = TARGET_ROOT / "preview_vortex_vehicle.png"
bpy.context.scene.render.filepath = str(out_vh)
bpy.ops.render.render(write_still=True)
print(f"[OK] Rendered {out_vh}")

# 3. Render Weapons Preview
print("\n--- Rendering Weapons Preview ---")
bpy.ops.wm.open_mainfile(filepath=str(WPN_BLEND))
setup_studio_lighting_and_cam(cam_loc=(0, -5.0, 2.0), cam_rot=(75, 0, 0), cam_lens=45)
out_wpn = TARGET_ROOT / "preview_vortex_weapons.png"
bpy.context.scene.render.filepath = str(out_wpn)
bpy.ops.render.render(write_still=True)
print(f"[OK] Rendered {out_wpn}")

print("\n[SUCCESS] Previews generated successfully!")
