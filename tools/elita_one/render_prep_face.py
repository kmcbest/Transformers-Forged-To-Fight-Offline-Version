import bpy

fbx_prep = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"
out_img = r"E:\Agent\TFTF-blender\preview_prep_face.png"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_prep)

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
# Head is at Y ~ 7.6
cam.location = (0, 3, 7.6)
cam.rotation_euler = (1.5708, 0, 3.14159)
bpy.context.scene.camera = cam

bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 800
bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.display.shading.light = 'STUDIO'
bpy.context.scene.display.shading.color_type = 'MATERIAL'

bpy.context.scene.render.filepath = out_img
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered {out_img}")
