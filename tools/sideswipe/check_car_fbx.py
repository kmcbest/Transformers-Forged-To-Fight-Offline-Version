import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy

CAR_FBX = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\03_fbx_exports\sideswipe_vh_prepared.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=CAR_FBX)

mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
car = mesh_objs[0]

# Check vertices with min Y (-5.54) and max Y (+5.66)
# The front hood of Corvette Stingray has a pointy nose, rear has spoiler/quad exhausts
all_v = car.data.vertices
min_y_pts = [v.co for v in all_v if v.co.y < -4.5]
max_y_pts = [v.co for v in all_v if v.co.y > 4.5]

print(f"At min Y (around -5.0m): Z range = [{min(p.z for p in min_y_pts):.2f}, {max(p.z for p in min_y_pts):.2f}], X width = {max(p.x for p in min_y_pts) - min(p.x for p in min_y_pts):.2f}")
print(f"At max Y (around +5.0m): Z range = [{min(p.z for p in max_y_pts):.2f}, {max(p.z for p in max_y_pts):.2f}], X width = {max(p.x for p in max_y_pts) - min(p.x for p in max_y_pts):.2f}")
