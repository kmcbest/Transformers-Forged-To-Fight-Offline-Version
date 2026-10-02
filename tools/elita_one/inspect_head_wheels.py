import bpy

fbx_prep = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_prep)

m = bpy.data.objects['cha_elita_one_gs_00']
head_verts = [v for v in m.data.vertices if v.co.z > 7.0]
print(f"Total head verts (Z > 7.0m): {len(head_verts)}")
# Find max/min coordinates of head
z_max = max(v.co.z for v in head_verts)
y_range = (min(v.co.y for v in head_verts), max(v.co.y for v in head_verts))
x_range = (min(v.co.x for v in head_verts), max(v.co.x for v in head_verts))
print(f"Head bbox: Z max = {z_max:.2f}, Y = {y_range}, X = {x_range}")

# Check wheels / tires in SK_CH_11.001
# Are there wheels in SK_CH_11.001?
for vg in m.vertex_groups:
    if 'wheel' in vg.name.lower():
        print(f"Wheel VG: {vg.name}")
