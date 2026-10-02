import bpy

fbx_prep = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_prep)

m = bpy.data.objects['cha_elita_one_gs_00']

# Let's inspect polygons around Y in [7.3, 7.8], X in [-0.3, 0.3], Z in [-0.5, 0.5]
face_candidates = []
for p in m.data.polygons:
    pts = [m.data.vertices[v].co for v in p.vertices]
    avg_x = sum(pt.x for pt in pts) / len(pts)
    avg_y = sum(pt.y for pt in pts) / len(pts)
    avg_z = sum(pt.z for pt in pts) / len(pts)
    if 7.3 < avg_y < 7.8 and abs(avg_x) < 0.3 and abs(avg_z) < 0.5:
        face_candidates.append((p, avg_x, avg_y, avg_z))

print(f"Face candidates count: {len(face_candidates)}")
mat_map = {}
for p, x, y, z in face_candidates:
    mat_map[p.material_index] = mat_map.get(p.material_index, 0) + 1
print(f"Material index in face: {mat_map}")
