import bpy
import math

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

cam = bpy.data.objects.get("FrontCam")
# Move camera to +Y looking towards -Y (Front of Arcee)
cam.location = (0.0, 18.5, 4.4)
cam.rotation_euler = (math.radians(90.0), 0.0, math.radians(180.0))

bpy.context.scene.frame_set(0)
bpy.context.view_layer.update()

out_path = r"C:\Users\Xiangli496\.gemini\antigravity\brain\db8b7cf0-602b-4ceb-a715-2db112ce44ce\test_front_view_00.png"
bpy.context.scene.render.filepath = out_path
bpy.ops.render.render(write_still=True)
print(f"Rendered front view to {out_path}")
