import bpy
from pathlib import Path
import mathutils

fbx_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
print(f"Total mesh objects: {len(mesh_objs)}")
for obj in mesh_objs:
    mesh = obj.data
    print(f"Mesh: {obj.name}, vertices: {len(mesh.vertices)}, polygons: {len(mesh.polygons)}")
    
    # Check normals
    inward_count = 0
    center = sum((v.co for v in mesh.vertices), mathutils.Vector()) / len(mesh.vertices)
    for p in mesh.polygons:
        # Vector from center to polygon center
        poly_center = p.center
        v_out = (poly_center - center).normalized()
        # If dot product of normal and v_out < -0.2, likely facing inward
        if p.normal.dot(v_out) < -0.3:
            inward_count += 1
    print(f"  Likely inverted/inward-facing polygons: {inward_count} / {len(mesh.polygons)} ({inward_count/len(mesh.polygons)*100:.1f}%)")
