import bpy

fbx_raw = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_raw)

m = bpy.data.objects['SK_CH_11.001']

# Check face vertices UVs and their material slot in the RAW FBX
uv_layer = m.data.uv_layers.active.data
face_materials = set()
face_uvs = []

for p in m.data.polygons:
    pts = [m.data.vertices[v].co for v in p.vertices]
    # In raw FBX, check where head is
    # What are dimensions of m in raw FBX?
    avg_z = sum(pt.z for pt in pts) / len(pts)
    avg_y = sum(pt.y for pt in pts) / len(pts)
    avg_x = sum(pt.x for pt in pts) / len(pts)
    if avg_z > 7.0: # head
        face_materials.add(m.data.materials[p.material_index].name)
        for loop_idx in p.loop_indices:
            uv = uv_layer[loop_idx].uv
            face_uvs.append(uv)

print("Face materials in RAW FBX:", face_materials)
print(f"Face UV count: {len(face_uvs)}")
if face_uvs:
    u_min = min(uv.x for uv in face_uvs)
    u_max = max(uv.x for uv in face_uvs)
    v_min = min(uv.y for uv in face_uvs)
    v_max = max(uv.y for uv in face_uvs)
    print(f"Face UV bounds: U[{u_min:.3f}, {u_max:.3f}], V[{v_min:.3f}, {v_max:.3f}]")
