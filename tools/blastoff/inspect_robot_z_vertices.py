import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\03_fbx_exports\blastoff_robot_prepared.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
for o in mesh_objs:
    print(f"Object: {o.name}")
    vs = o.data.vertices
    xs = [(o.matrix_world @ v.co).x for v in vs]
    ys = [(o.matrix_world @ v.co).y for v in vs]
    zs = [(o.matrix_world @ v.co).z for v in vs]
    print(f"  World X: [{min(xs):.3f}, {max(xs):.3f}]")
    print(f"  World Y: [{min(ys):.3f}, {max(ys):.3f}]")
    print(f"  World Z: [{min(zs):.3f}, {max(zs):.3f}]")

    # Find which vertices have Z < 0.5 or Z > 12.0
    low_z = [(i, (o.matrix_world @ v.co)) for i, v in enumerate(vs) if (o.matrix_world @ v.co).z < 0.2]
    high_z = [(i, (o.matrix_world @ v.co)) for i, v in enumerate(vs) if (o.matrix_world @ v.co).z > 12.0]
    print(f"  Num vertices with Z < 0.2: {len(low_z)}")
    print(f"  Num vertices with Z > 12.0: {len(high_z)}")

    # Check vertex groups of low_z vertices
    vg_names = {vg.index: vg.name for vg in o.vertex_groups}
    low_groups = {}
    for vi, co in low_z:
        for g in vs[vi].groups:
            gname = vg_names.get(g.group, "unknown")
            low_groups[gname] = low_groups.get(gname, 0) + 1
    print("  Low Z vertex groups:", sorted(low_groups.items(), key=lambda x: -x[1])[:10])

    high_groups = {}
    for vi, co in high_z:
        for g in vs[vi].groups:
            gname = vg_names.get(g.group, "unknown")
            high_groups[gname] = high_groups.get(gname, 0) + 1
    print("  High Z vertex groups:", sorted(high_groups.items(), key=lambda x: -x[1])[:10])
