import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\Blitzwing_EW\01_source\H_shandian_G1_M_LOD.fbx")

arm = bpy.data.objects["floor"]
arm.data.pose_position = 'REST'
bpy.context.view_layer.update()

for name, label in [("H_shandian_G1_W1_Lod", "SWORD"), ("H_shandian_G1_W2_Lod", "GUN")]:
    obj = bpy.data.objects[name]
    deps = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(deps)
    me = ev.to_mesh()
    pts = [ev.matrix_world @ v.co for v in me.vertices]
    # Print cross-section profile along Z for Sword and along X for Gun
    print(f"\n=== {label} ({name}) Profile ===")
    zs = sorted(p.z for p in pts)
    xs = sorted(p.x for p in pts)
    ys = sorted(p.y for p in pts)
    print(f"X=[{xs[0]:.5f}, {xs[-1]:.5f}], Y=[{ys[0]:.5f}, {ys[-1]:.5f}], Z=[{zs[0]:.5f}, {zs[-1]:.5f}]")
    if label == "SWORD":
        # Slice in 10 Z bands
        zmin, zmax = zs[0], zs[-1]
        for i in range(10):
            lo = zmin + i * (zmax - zmin) / 10
            hi = zmin + (i + 1) * (zmax - zmin) / 10
            band = [p for p in pts if lo <= p.z <= hi]
            if band:
                print(f"  Z[{lo:.4f},{hi:.4f}] n={len(band):3d} X=[{min(p.x for p in band):.4f},{max(p.x for p in band):.4f}] Y=[{min(p.y for p in band):.4f},{max(p.y for p in band):.4f}]")
    else:
        # Gun: slice in 10 X bands and 10 Z bands
        xmin, xmax = xs[0], xs[-1]
        for i in range(10):
            lo = xmin + i * (xmax - xmin) / 10
            hi = xmin + (i + 1) * (xmax - xmin) / 10
            band = [p for p in pts if lo <= p.x <= hi]
            if band:
                print(f"  X[{lo:.4f},{hi:.4f}] n={len(band):3d} Y=[{min(p.y for p in band):.4f},{max(p.y for p in band):.4f}] Z=[{min(p.z for p in band):.4f},{max(p.z for p in band):.4f}]")
    ev.to_mesh_clear()
