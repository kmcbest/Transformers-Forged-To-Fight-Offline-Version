import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

print(f"Total objects: {len(bpy.data.objects)}")
for o in bpy.data.objects:
    if o.type == 'MESH':
        mats = [m.name for m in o.data.materials if m]
        # Calculate bounding box
        coords = [v.co for v in o.data.vertices]
        if not coords:
            continue
        xs = [c.x for c in coords]
        ys = [c.y for c in coords]
        zs = [c.z for c in coords]
        # In blender FBX import: check if around chest (Z between 12 and 18, Y near 0, X between -5 and 5)
        print(f"Mesh '{o.name}': {len(o.data.vertices)} verts, {len(o.data.polygons)} polys, mats={mats}")
        print(f"   X: [{min(xs):.2f}, {max(xs):.2f}], Y: [{min(ys):.2f}, {max(ys):.2f}], Z: [{min(zs):.2f}, {max(zs):.2f}]")
