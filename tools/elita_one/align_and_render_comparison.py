import bpy
import math
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BLEND_FILE = ROOT / "tools" / "elita_one" / "elita_one_arcee_setup.blend"

bpy.ops.wm.open_mainfile(filepath=str(BLEND_FILE))

arcee = bpy.data.objects.get("Arcee_Ghost_Reference")
elita_mesh = bpy.data.objects.get("Elita_One_Mesh")
elita_arm = bpy.data.objects.get("Elita_One_Armature")

# Reset Elita location
elita_arm.location = (0.0, 0.0, 0.0)
elita_mesh.location = (0.0, 0.0, 0.0)

# Rotate Elita One by -90 degrees around Z so shoulders align along X
elita_arm.rotation_euler = (0.0, 0.0, math.radians(-90.0))
bpy.context.view_layer.objects.active = elita_arm
bpy.ops.object.select_all(action='DESELECT')
elita_arm.select_set(True)
elita_mesh.select_set(True)
bpy.ops.object.transform_apply(rotation=True)

# Now check shoulder axis
l_arm = elita_arm.data.bones.get('l_upperarm_skin')
r_arm = elita_arm.data.bones.get('r_upperarm_skin')
print(f"New shoulder vector: {l_arm.head_local - r_arm.head_local}")

# Position side-by-side: Elita on left (X = -2.5m), Arcee on right (X = +2.5m)
elita_arm.location = (-2.5, 0.0, 0.0)
elita_mesh.location = (-2.5, 0.0, 0.0)
arcee.location = (2.5, 0.0, 0.0)

# Camera: frame both full characters from head to toe
cam_obj = bpy.data.objects.get("FrontCam")
cam_obj.location = (0.0, -18.0, 4.4)
cam_obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
cam_obj.data.lens = 42

# Render full comparison
out_img = ROOT / "tools" / "elita_one" / "preview_elita_arcee_comparison.png"
bpy.context.scene.render.filepath = str(out_img)
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered side-by-side comparison to {out_img}")

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_FILE))
print(f"[✓] Saved updated setup blend to {BLEND_FILE}")
