import bpy

fbx_prep = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"
fbx_raw = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"

# Check face polygon normals in prepared vs raw!
def check_face_normals(fbx_file, name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fbx_file)
    mesh_obj = None
    for o in bpy.data.objects:
        if o.type == 'MESH':
            mesh_obj = o
            break
    
    # Face is in head region (front)
    # Find polygons in face
    face_normals_z = []
    face_normals_y = []
    for p in mesh_obj.data.polygons:
        pts = [mesh_obj.data.vertices[v].co for v in p.vertices]
        avg_y = sum(pt.y for pt in pts) / len(pts)
        avg_z = sum(pt.z for pt in pts) / len(pts)
        avg_x = sum(pt.x for pt in pts) / len(pts)
        # In prepared FBX, Y is up (~7.5), X is around 0.
        # Let's check:
        if abs(avg_x) < 0.2:
            if avg_y > 7.3: # Y-up
                face_normals_z.append(p.normal.z)
            elif avg_z > 7.3: # Z-up
                face_normals_y.append(p.normal.y)
    
    print(f"=== {name} ===")
    if face_normals_z:
        avg_nz = sum(face_normals_z) / len(face_normals_z)
        print(f"  Face normals Z (Y-up): count={len(face_normals_z)}, avg_nz={avg_nz:.3f}")
        print(f"  Positive Z count: {sum(1 for n in face_normals_z if n > 0)}, Negative Z count: {sum(1 for n in face_normals_z if n < 0)}")
    if face_normals_y:
        avg_ny = sum(face_normals_y) / len(face_normals_y)
        print(f"  Face normals Y (Z-up): count={len(face_normals_y)}, avg_ny={avg_ny:.3f}")
        print(f"  Positive Y count: {sum(1 for n in face_normals_y if n > 0)}, Negative Y count: {sum(1 for n in face_normals_y if n < 0)}")

check_face_normals(fbx_raw, "RAW FBX")
check_face_normals(fbx_prep, "PREPARED FBX")
