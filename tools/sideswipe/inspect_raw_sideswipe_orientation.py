import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
import math

ROBOT_FBX = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=ROBOT_FBX)

mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
for a in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
    bpy.data.objects.remove(a, do_unlink=True)
for o in mesh_objs:
    o.modifiers.clear()

print("Before rotate:")
for o in mesh_objs[:2]:
    print(f"  {o.name}: loc={o.location}, rot={o.rotation_euler}, scale={o.scale}")

bpy.ops.object.select_all(action='DESELECT')
for o in mesh_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = mesh_objs[0]

bpy.ops.transform.rotate(value=math.pi, orient_axis='X')
print("After rotate:")
for o in mesh_objs[:2]:
    print(f"  {o.name}: loc={o.location}, rot={o.rotation_euler}, scale={o.scale}")

bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
print("After transform_apply:")
for o in mesh_objs[:2]:
    print(f"  {o.name}: loc={o.location}, rot={o.rotation_euler}, scale={o.scale}")

for o in mesh_objs:
    if o.name == "20":
        pts = [v.co for v in o.data.vertices]
        print(f"Mesh 20 (chest headlights) pos after apply: ({sum(p.x for p in pts)/len(pts):.3f}, {sum(p.y for p in pts)/len(pts):.3f}, {sum(p.z for p in pts)/len(pts):.3f})")
