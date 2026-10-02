import bpy

fbx_prep = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_prep)

m = bpy.data.objects['cha_elita_one_gs_00']

# Let's inspect the face:
# In Y-up:
# Face is around Y in [7.3, 8.0]
# Is Z positive or negative for front?
# Let's check Z values of chest vs back
chest_y = [v.co.z for v in m.data.vertices if 5.5 < v.co.y < 6.5]
print(f"Chest Z range: min={min(chest_y):.2f}, max={max(chest_y):.2f}")
# If chest extends more towards -Z or +Z?
# In Blender view, car hood is on the back!
