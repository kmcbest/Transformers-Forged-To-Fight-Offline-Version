import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.obj")

car = bpy.data.objects['strongarm_vehicle']
car.rotation_euler = (1.5707963, 0, 0)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
car.scale = (1.0, 1.45168, 1.073)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

bpy.ops.mesh.separate(type='LOOSE')
parts = [o for o in bpy.data.objects if o.type == 'MESH']

wheel_candidates = []
for p in parts:
    verts = p.data.vertices
    cx = sum(v.co.x for v in verts) / len(verts)
    cy = sum(v.co.y for v in verts) / len(verts)
    cz = sum(v.co.z for v in verts) / len(verts)
    if cz < 1.0 and abs(cx) > 0.8:
        wheel_candidates.append((p.name, cx, cy, cz, len(verts)))

print(f"Parts at wheel height ({len(wheel_candidates)}):")
for name, cx, cy, cz, cnt in wheel_candidates[:12]:
    print(f"  {name:25s}: ({cx:.3f}, {cy:.3f}, {cz:.3f}) with {cnt} verts")
