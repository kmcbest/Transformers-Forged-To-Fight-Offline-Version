import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

blend_path = r"E:\Agent\TFTF-blender\3rd-party-models\blitzwing_extracted\rar\Blitzwing.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

print("Objects in Blitzwing.blend:")
for o in bpy.data.objects:
    print(f"  {o.name}: type={o.type}, parent={o.parent.name if o.parent else None}")
    if o.type == 'MESH':
        bbox = [list(c) for c in o.bound_box]
        xs = [c[0] for c in bbox]
        ys = [c[1] for c in bbox]
        zs = [c[2] for c in bbox]
        print(f"    BBox X: [{min(xs):.3f}, {max(xs):.3f}], Y: [{min(ys):.3f}, {max(ys):.3f}], Z: [{min(zs):.3f}, {max(zs):.3f}]")
        print(f"    Materials: {[m.name for m in o.data.materials if m]}")
