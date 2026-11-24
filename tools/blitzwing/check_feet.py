import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

script = """
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath='toolchain/unity_build_project/Assets/Blitzwing/blitzwing_robot.fbx')
m = next(o for o in bpy.data.objects if o.type == 'MESH')
for bn in ['LeftFoot', 'LeftToeBase', 'RightFoot', 'RightToeBase']:
    if bn in m.vertex_groups:
        vg = m.vertex_groups[bn]
        cnt = sum(1 for v in m.data.vertices for g in v.groups if g.group == vg.index and g.weight > 0.05)
        print(f'{bn}: {cnt} verts')
    else:
        print(f'{bn}: NOT IN VERTEX GROUPS')
"""
Path("tools/blitzwing/inspect_feet_weights.py").write_text(script, encoding="utf-8")
