import bpy

fbx_raw = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"
out_img = r"E:\Agent\TFTF-blender\preview_raw_sketchfab.png"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_raw)

# Keep only SK_CH_11.001
for o in list(bpy.context.scene.collection.objects):
    if o.name != "SK_CH_11.001":
        bpy.data.objects.remove(o, do_unlink=True)

# Add camera looking at front of SK_CH_11.001
# In raw FBX, front is -X or +X? Let's check:
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = (8, 0, 4.4) # looking along -X
cam.rotation_euler = (1.5708, 0, 1.5708)
bpy.context.scene.camera = cam

bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 1000
bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.display.shading.light = 'STUDIO'
bpy.context.scene.display.shading.color_type = 'TEXTURE'

bpy.context.scene.render.filepath = out_img
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered raw sketchfab front: {out_img}")
