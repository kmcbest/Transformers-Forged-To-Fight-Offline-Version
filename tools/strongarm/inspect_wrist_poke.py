import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\strongarm_prepared.fbx")
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')

# Inspect vertices in Left hand / wrist area (X > 1.8, 3.8 < Z < 4.9) grouped by dominant bone
groups = {}
for v in mesh.data.vertices:
    if v.co.x > 1.8 and 3.8 < v.co.z < 5.0:
        best = None
        for g in v.groups:
            bn = mesh.vertex_groups[g.group].name
            if best is None or g.weight > best[1]:
                best = (bn, g.weight)
        bn = best[0] if best else "NONE"
        groups.setdefault(bn, []).append(v.co)

for bn, pts in sorted(groups.items()):
    zs = [p.z for p in pts]; xs = [p.x for p in pts]; ys = [p.y for p in pts]
    print(f"  {bn:18s} ({len(pts):4d} verts): X=[{min(xs):+.3f},{max(xs):+.3f}] Y=[{min(ys):+.3f},{max(ys):+.3f}] Z=[{min(zs):+.3f},{max(zs):+.3f}]")
