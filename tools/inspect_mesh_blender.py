import bpy
import sys
from pathlib import Path

obj_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\OptimusPrime\cha_optimusprime_gs_voyager2015_00.obj"

# Reset scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Import OBJ
bpy.ops.wm.obj_import(filepath=obj_path)

objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
print(f"Imported {len(objs)} mesh objects:")
for o in objs:
    print(f"  Object: {o.name}, Verts: {len(o.data.vertices)}, Polys: {len(o.data.polygons)}")
    # Check bounding box
    bbox = [o.matrix_world @ o.bound_box[i] for i in range(8)]
    min_z = min(b.z for b in bbox)
    max_z = max(b.z for b in bbox)
    min_y = min(b.y for b in bbox)
    max_y = max(b.y for b in bbox)
    print(f"  Y range: {min_y:.2f} to {max_y:.2f}, Z range: {min_z:.2f} to {max_z:.2f}")
