import bpy
import math
import mathutils
from pathlib import Path

ROOT = Path("tools/demolishor")
BLEND_PATH = ROOT / "demolishor_phase2_inspect.blend"
bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))

# Add Full-Body Front Camera (viewing from Y=14, looking towards -Y at center)
cam_data = bpy.data.cameras.new("FrontCam")
cam_obj = bpy.data.objects.new("FrontCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

cam_obj.location = (0.0, 14.0, 5.5)
direction = mathutils.Vector((0, 0, 5.5)) - cam_obj.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()

bpy.context.scene.render.resolution_x = 900
bpy.context.scene.render.resolution_y = 1000

# Render frame 0 (Natural standing pose)
bpy.context.scene.frame_current = 0
bpy.context.scene.render.filepath = str(ROOT.resolve() / "preview_front_standing.png")
bpy.ops.render.render(write_still=True)

# Render frame 10 (Full body sprint)
bpy.context.scene.frame_current = 10
bpy.context.scene.render.filepath = str(ROOT.resolve() / "preview_front_running.png")
bpy.ops.render.render(write_still=True)

print("[✓] Rendered front standing and running previews!")
