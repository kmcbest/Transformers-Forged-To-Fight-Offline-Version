import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
from mathutils import Vector
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
ALIGNED_DIR = ROOT / "3rd-party-models" / "Swindle" / "01_aligned_mesh"
RENDERS_DIR = ROOT / "renders" / "swindle"
RENDERS_DIR.mkdir(parents=True, exist_ok=True)

out_png = RENDERS_DIR / "gate2_blender_robot_sbs.png"

bpy.ops.wm.read_factory_settings(use_empty=True)

# Scene settings
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.eevee.use_gtao = True
scene.eevee.use_bloom = True

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.08, 0.09, 0.12, 1.0)

# Import Robot FBX
fbx_r = ROOT / "3rd-party-models" / "Swindle" / "03_fbx_exports" / "swindle_robot_prepared.fbx"
bpy.ops.import_scene.fbx(filepath=str(fbx_r))
arm_r = bpy.context.active_object
arm_r.location = (-4.0, 0.0, 0.0)

# Import Vehicle FBX
fbx_v = ROOT / "3rd-party-models" / "Swindle" / "03_fbx_exports" / "swindle_veh_prepared.fbx"
bpy.ops.import_scene.fbx(filepath=str(fbx_v))
arm_v = bpy.context.active_object
arm_v.location = (4.0, 0.0, 0.0)

# Lighting
key_l = bpy.data.lights.new("KeyLight", 'SUN')
key_l.energy = 2.5
key_l.color = (1.0, 0.98, 0.92)
k_obj = bpy.data.objects.new("KeyLight", key_l)
scene.collection.objects.link(k_obj)
k_obj.rotation_euler = (math.radians(45.0), math.radians(20.0), math.radians(-30.0))

fill_l = bpy.data.lights.new("FillLight", 'SUN')
fill_l.energy = 1.2
fill_l.color = (0.85, 0.90, 1.0)
f_obj = bpy.data.objects.new("FillLight", fill_l)
scene.collection.objects.link(f_obj)
f_obj.rotation_euler = (math.radians(35.0), math.radians(-15.0), math.radians(140.0))

# Camera
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 40.0
cam_obj = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj
cam_obj.location = (0.0, -25.0, 5.2)
cam_obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)

scene.render.filepath = str(out_png)
print(f"Rendering {out_png}...")
bpy.ops.render.render(write_still=True)
print("[✓] Gate 2 Blender SBS Render Complete!")
