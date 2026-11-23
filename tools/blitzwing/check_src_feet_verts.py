import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path

script = """
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath='3rd-party-models/Blitzwing_EW/01_source/H_shandian_G1_M_LOD.fbx')
m = next(o for o in bpy.data.objects if o.type == 'MESH')
for bn in ['Bone006(mirrored)', 'Bone007(mirrored)', 'Bone008(mirrored)', 'Bone009(mirrored)', 'Bip001 L Foot']:
    if bn in m.vertex_groups:
        vg = m.vertex_groups[bn]
        vs = [v.co for v in m.data.vertices for g in v.groups if g.group == vg.index and g.weight > 0.1]
        if vs:
            min_y = min(co.y for co in vs)
            max_y = max(co.y for co in vs)
            min_z = min(co.z for co in vs)
            max_z = max(co.z for co in vs)
            print(f'{bn}: {len(vs)} verts, Y=[{min_y:.3f}, {max_y:.3f}], Z=[{min_z:.3f}, {max_z:.3f}]')
        else:
            print(f'{bn}: 0 verts')
"""
Path("tools/blitzwing/inspect_source_feet_verts.py").write_text(script, encoding="utf-8")
