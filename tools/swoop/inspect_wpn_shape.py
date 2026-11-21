import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

wpn = bpy.data.objects.get("Swoop_Weapon")
pts = [v.co for v in wpn.data.vertices]
xs = [p.x for p in pts]
ys = [p.y for p in pts]
zs = [p.z for p in pts]
print(f"Swoop_Weapon local bounding box: X=[{min(xs):.4f}, {max(xs):.4f}], Y=[{min(ys):.4f}, {max(ys):.4f}], Z=[{min(zs):.4f}, {max(zs):.4f}]")
print(f"Span: X={max(xs)-min(xs):.4f}, Y={max(ys)-min(ys):.4f}, Z={max(zs)-min(zs):.4f}")
