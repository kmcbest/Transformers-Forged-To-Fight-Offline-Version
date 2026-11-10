import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.obj")

car = bpy.data.objects['strongarm_vehicle']
verts = car.data.vertices
print(f"Vehicle raw OBJ bounds:")
print(f"X: [{min(v.co.x for v in verts):.3f}, {max(v.co.x for v in verts):.3f}]")
print(f"Y: [{min(v.co.y for v in verts):.3f}, {max(v.co.y for v in verts):.3f}]")
print(f"Z: [{min(v.co.z for v in verts):.3f}, {max(v.co.z for v in verts):.3f}]")
