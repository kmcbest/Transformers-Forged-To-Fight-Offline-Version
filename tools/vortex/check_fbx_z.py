import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\vortex_prepared.fbx")

mesh = bpy.data.objects.get("cha_vortex_gs_00")
if mesh:
    # Check min Z per vertex group
    for vg in mesh.vertex_groups:
        v_indices = [v.index for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.5 for g in v.groups)]
        if v_indices:
            zs = [mesh.data.vertices[i].co.z for i in v_indices]
            if min(zs) < 0.2:
                print(f"VG {vg.name:15s} ({len(v_indices)} verts): min Z = {min(zs):.3f}, max Z = {max(zs):.3f}")
