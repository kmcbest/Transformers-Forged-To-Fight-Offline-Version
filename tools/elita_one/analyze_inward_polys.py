import bpy
import mathutils

fbx_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_obj = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
mesh = mesh_obj.data

# Check vertex groups for inward-facing polygons
vg_names = [vg.name for vg in mesh_obj.vertex_groups]
poly_by_bone = {}

center = sum((v.co for v in mesh.vertices), mathutils.Vector()) / len(mesh.vertices)
for p in mesh.polygons:
    v_out = (p.center - center).normalized()
    if p.normal.dot(v_out) < -0.3:
        # Check dominant bone for this polygon
        bones_in_poly = []
        for v_idx in p.vertices:
            v = mesh.vertices[v_idx]
            for g in v.groups:
                if g.group < len(vg_names):
                    bones_in_poly.append(vg_names[g.group])
        dominant_bone = max(set(bones_in_poly), key=bones_in_poly.count) if bones_in_poly else "Unknown"
        poly_by_bone[dominant_bone] = poly_by_bone.get(dominant_bone, 0) + 1

print("Inward-facing polygons by dominant bone (Top 20):")
for b, cnt in sorted(poly_by_bone.items(), key=lambda x: x[1], reverse=True)[:20]:
    print(f"  {b:25s}: {cnt} polygons")
