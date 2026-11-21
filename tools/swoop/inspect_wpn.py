import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

wpn = bpy.data.objects.get("Swoop_Weapon")
if wpn:
    print(f"Swoop_Weapon parent: {wpn.parent.name if wpn.parent else None}")
    print(f"Swoop_Weapon vertex count: {len(wpn.data.vertices)}")
    print(f"Swoop_Weapon vertex groups: {[vg.name for vg in wpn.vertex_groups]}")
    # Check bounds
    pts = [v.co for v in wpn.data.vertices]
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    zs = [p.z for p in pts]
    print(f"Local bounds: X=[{min(xs):.4f}, {max(xs):.4f}], Y=[{min(ys):.4f}, {max(ys):.4f}], Z=[{min(zs):.4f}, {max(zs):.4f}]")
