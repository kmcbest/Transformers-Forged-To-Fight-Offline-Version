import bpy
import math
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"
OUT_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\db8b7cf0-602b-4ceb-a715-2db112ce44ce")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

# Check all objects
for o in bpy.data.objects:
    print(f"Object in scene: {o.name}, type={o.type}")

# Hide or remove vehicle
for o in list(bpy.data.objects):
    if "TR" in o.name:
        bpy.data.objects.remove(o, do_unlink=True)

# Setup camera
cam_data = bpy.data.cameras.new("Cam")
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# In FBX coordinates:
# Model forward is +X, Left is +Y, Up is +Z
# Look from front (+X) towards -X:
cam_obj.location = (20.0, 0.0, 4.2)
cam_obj.rotation_euler = (math.radians(90.0), 0.0, math.radians(90.0))

# Lights
light_key = bpy.data.lights.new(name="Sun", type='SUN')
light_key.energy = 4.0
light_obj = bpy.data.objects.new(name="Sun", object_data=light_key)
bpy.context.scene.collection.objects.link(light_obj)
light_obj.rotation_euler = (math.radians(45.0), math.radians(45.0), 0.0)

bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.display.shading.light = 'STUDIO'
bpy.context.scene.display.shading.color_type = 'TEXTURE'
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080

bpy.context.scene.render.filepath = str(OUT_DIR / "fbx_raw_front.png")
bpy.ops.render.render(write_still=True)
print("[✓] Rendered fbx_raw_front.png")
