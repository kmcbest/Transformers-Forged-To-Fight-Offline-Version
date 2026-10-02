import bpy
from pathlib import Path

fbx_prep = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"
out_img = r"E:\Agent\TFTF-blender\preview_prep_mesh.png"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_prep)

# Add camera
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = (0, -10, 4.4)
cam.rotation_euler = (1.5708, 0, 0)
bpy.context.scene.camera = cam

# Set render settings
bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 1000
bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.display.shading.light = 'STUDIO'
bpy.context.scene.display.shading.color_type = 'MATERIAL'

bpy.context.scene.render.filepath = out_img
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered {out_img}")
