import bpy
import bmesh

# 1. Check Robot FBX simple flip_normals in Blender
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\strongarm_prepared.fbx")
for o in bpy.data.objects:
    if o.type == 'MESH':
        me = o.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        # Note: if custom split normals exist, reverse them too or recalc smooth!
        me.calc_normals_split()
        max_x = max(v.co.x for v in me.vertices)
        px_p, px_l = [], []
        for poly in me.polygons:
            if poly.center.x > max_x - 0.35 and abs(poly.normal.x) > 0.5:
                px_p.append(poly.normal.x)
                for li in poly.loop_indices:
                    px_l.append(me.loops[li].normal.x)
        print(f"Robot AFTER reverse_faces: Outer+X poly.n.x={sum(px_p)/len(px_p):.3f}, loop.n.x={sum(px_l)/len(px_l):.3f}")

# 2. Check Vehicle OBJ UV preservation under bmesh remove_doubles(dist=0.0002)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.obj(filepath=r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.obj")
vh = [o for o in bpy.data.objects if o.type == 'MESH'][0]
uv_lay = vh.data.uv_layers.active
before = {}
for poly in vh.data.polygons:
    key = tuple(round(x, 4) for x in poly.center)
    uvs = tuple(sorted((round(uv_lay.data[li].uv.x, 4), round(uv_lay.data[li].uv.y, 4)) for li in poly.loop_indices))
    before[key] = uvs

bm = bmesh.new()
bm.from_mesh(vh.data)
fc_before = len(bm.faces)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0002)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
fc_after = len(bm.faces)
bm.to_mesh(vh.data)
bm.free()
vh.data.update()

uv_lay = vh.data.uv_layers.active
after = {}
for poly in vh.data.polygons:
    key = tuple(round(x, 4) for x in poly.center)
    uvs = tuple(sorted((round(uv_lay.data[li].uv.x, 4), round(uv_lay.data[li].uv.y, 4)) for li in poly.loop_indices))
    after[key] = uvs

matched = sum(1 for k, v in before.items() if after.get(k) == v)
print(f"Vehicle OBJ faces: {fc_before} -> {fc_after}, UV-identical polygons: {matched}/{len(before)}")
