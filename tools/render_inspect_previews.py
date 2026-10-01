import bpy
import math
import mathutils
from pathlib import Path

ROOT = Path("tools/demolishor")
BLEND_PATH = ROOT / "demolishor_phase2_inspect.blend"
bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))

# Setup 3/4 Front-Side Camera (View from front-right)
cam_data = bpy.data.cameras.new("InspectCam")
cam_obj = bpy.data.objects.new("InspectCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# Camera at X=7.0, Y=11.0, Z=6.5 (Looking down-left towards character at center)
cam_obj.location = (7.0, 11.0, 6.5)
direction = mathutils.Vector((0, 0, 5.5)) - cam_obj.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()

# Sun Light
light_data = bpy.data.lights.new("MainSun", type='SUN')
light_obj = bpy.data.objects.new("MainSun", light_data)
bpy.context.scene.collection.objects.link(light_obj)
light_obj.location = (5, 10, 15)
light_obj.rotation_euler = (math.radians(-35), math.radians(25), math.radians(110))
light_data.energy = 3.5

bpy.context.scene.render.resolution_x = 900
bpy.context.scene.render.resolution_y = 1000

# Hide ghost reference from render
ghost = bpy.data.objects.get("Ironhide_Ghost_Reference")
if ghost:
    ghost.hide_render = True

# Frame 0: Rest pose
bpy.context.scene.frame_current = 0
bpy.context.scene.render.filepath = str(ROOT.resolve() / "preview_rest_pose.png")
bpy.ops.render.render(write_still=True)

# Frame 20: Arm swinging forward
bpy.context.scene.frame_current = 20
bpy.context.scene.render.filepath = str(ROOT.resolve() / "preview_stride_frame20.png")
bpy.ops.render.render(write_still=True)

# Frame 50: Opposite stride
bpy.context.scene.frame_current = 50
bpy.context.scene.render.filepath = str(ROOT.resolve() / "preview_stride_frame50.png")
bpy.ops.render.render(write_still=True)

print("[✓] Successfully rendered frames 0, 20, 50!")
