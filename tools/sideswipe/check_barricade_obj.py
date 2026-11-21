import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
from mathutils import Vector

BARR_OBJ = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\00_donor_reference\cha_barricade_cin_dotm_00_robot.obj"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.obj(filepath=BARR_OBJ)

barr = bpy.context.selected_objects[0]
print(f"Barricade OBJ imported: {barr.name}")
verts = [v.co for v in barr.data.vertices]
xs = [v.x for v in verts]
ys = [v.y for v in verts]
zs = [v.z for v in verts]
print(f"Barricade bounds: X=[{min(xs):.3f}, {max(xs):.3f}], Y=[{min(ys):.3f}, {max(ys):.3f}], Z=[{min(zs):.3f}, {max(zs):.3f}]")

# Let's find vertices with highest/lowest Y at head/chest level (Z ~ 8 to 10)
chest_verts = [v for v in verts if 7.5 < v.z < 9.0]
print(f"At chest level (Z=7.5-9.0), Y range: [{min(v.y for v in chest_verts):.3f}, {max(v.y for v in chest_verts):.3f}]")
