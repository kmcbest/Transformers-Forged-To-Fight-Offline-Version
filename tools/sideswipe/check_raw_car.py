import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy

CAR_RAW = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe_Car.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=CAR_RAW)

for o in bpy.data.objects:
    if o.type == 'MESH':
        all_v = [v.co for v in o.data.vertices]
        ys = [v.y for v in all_v]
        zs = [v.z for v in all_v]
        print(f"Raw Car {o.name:15s}: Y=[{min(ys):.2f}, {max(ys):.2f}], Z=[{min(zs):.2f}, {max(zs):.2f}]")
