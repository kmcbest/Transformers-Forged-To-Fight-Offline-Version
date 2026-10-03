import bpy

fbx_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

for obj in bpy.data.objects:
    if obj.type == "MESH":
        print(f"Mesh Object: {obj.name}, verts={len(obj.data.vertices)}, polys={len(obj.data.polygons)}")
        for idx, s in enumerate(obj.material_slots):
            polys = [p for p in obj.data.polygons if p.material_index == idx]
            print(f"  Slot {idx} ({s.name}): {len(polys)} polys")
            
        # Check where the eyes are in this mesh!
        # Search for eye polys: Z around 4.2m in Blender prepared FBX
        # In prepared FBX, is Z up or Y up?
        # Let's check bounding box
        bbox = [obj.matrix_world @ v.co for v in obj.data.vertices]
        min_co = [min(v[i] for v in bbox) for i in range(3)]
        max_co = [max(v[i] for v in bbox) for i in range(3)]
        print(f"  World bounds: min={min_co}, max={max_co}")
