import bpy
import bmesh

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.obj(filepath=r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.obj")
obj = [o for o in bpy.data.objects if o.type == 'MESH'][0]
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
obj.rotation_euler = (1.5707963, 0, 0)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Check UV before weld
uv_before = [tuple(round(x, 5) for x in l.uv) for l in obj.data.uv_layers.active.data]

# Weld spatially coincident vertices with bmesh (preserves loop UVs!)
bm = bmesh.new()
bm.from_mesh(obj.data)
before_v = len(bm.verts)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
after_v = len(bm.verts)
bm.to_mesh(obj.data)
bm.free()
obj.data.update()

uv_after = [tuple(round(x, 5) for x in l.uv) for l in obj.data.uv_layers.active.data]
print(f"Welded verts: {before_v} -> {after_v}, loops intact: {len(uv_before) == len(uv_after)}, exact UV match: {uv_before == uv_after}")

bpy.ops.mesh.separate(type='LOOSE')
parts = [o for o in bpy.data.objects if o.type == 'MESH']
print(f"Loose parts AFTER weld: {len(parts)}")
for i, p in enumerate(parts):
    vs = [p.matrix_world @ v.co for v in p.data.vertices]
    xs = [v.x for v in vs]; ys = [v.y for v in vs]; zs = [v.z for v in vs]
    cx, cy, cz = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2, (min(zs)+max(zs))/2
    sx, sy, sz = max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs)
    print(f"  Part[{i:2d}] verts={len(vs):4d} center=({cx:+.3f},{cy:+.3f},{cz:+.3f}) size=({sx:.3f},{sy:.3f},{sz:.3f})")
