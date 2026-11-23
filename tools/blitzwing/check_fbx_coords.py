import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path

# Let's inspect via Blender headless
script = """
import bpy
for p in ['blitzwing_robot.fbx', 'blitzwing_tank.fbx', 'blitzwing_jet.fbx']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath='toolchain/unity_build_project/Assets/Blitzwing/' + p)
    for o in bpy.data.objects:
        if o.type == 'MESH':
            xs = [v.co.x for v in o.data.vertices]
            ys = [v.co.y for v in o.data.vertices]
            zs = [v.co.z for v in o.data.vertices]
            print(f'{p} -> {o.name}: X=[{min(xs):.2f}, {max(xs):.2f}] Y=[{min(ys):.2f}, {max(ys):.2f}] Z=[{min(zs):.2f}, {max(zs):.2f}]')
"""
Path("tools/blitzwing/inspect_fbx_bounds.py").write_text(script, encoding="utf-8")
