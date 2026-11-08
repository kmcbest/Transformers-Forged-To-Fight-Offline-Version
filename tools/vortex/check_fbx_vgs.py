import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

fbx_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\vortex_vh_prepared.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        print(f"Object: {obj.name}, verts={len(obj.data.vertices)}")
        print(f"Vertex groups: {[vg.name for vg in obj.vertex_groups]}")
        # Count verts in rotor VGs
        for vg in obj.vertex_groups:
            if "rotor" in vg.name.lower() or "blade" in vg.name.lower() or "prop" in vg.name.lower():
                v_count = sum(1 for v in obj.data.vertices if any(g.group == vg.index and g.weight > 0.1 for g in v.groups))
                print(f"  {vg.name:25s}: {v_count} verts")

