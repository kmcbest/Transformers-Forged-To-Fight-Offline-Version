import bpy

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arcee_mesh = bpy.data.objects.get("Arcee_Mesh")
arcee_arm = bpy.data.objects.get("Arcee_Armature")
elita_mesh = bpy.data.objects.get("Elita_One_Mesh")
elita_arm = bpy.data.objects.get("Elita_One_Armature")

bpy.context.scene.frame_set(0)

# Render Arcee Alone
elita_mesh.hide_render = True
arcee_mesh.hide_render = False
bpy.context.scene.render.filepath = r"C:\Users\Xiangli496\.gemini\antigravity\brain\db8b7cf0-602b-4ceb-a715-2db112ce44ce\test_arcee_alone.png"
bpy.ops.render.render(write_still=True)

# Render Elita One Alone
elita_mesh.hide_render = False
arcee_mesh.hide_render = True
bpy.context.scene.render.filepath = r"C:\Users\Xiangli496\.gemini\antigravity\brain\db8b7cf0-602b-4ceb-a715-2db112ce44ce\test_elita_alone.png"
bpy.ops.render.render(write_still=True)

print("Rendered both individual isolation tests!")
