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
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for b in arm.data.bones:
    if any(k in b.name.lower() for k in ['foot', 'toe', 'bone006', 'bone007', 'bone008', 'bone009']):
        print(f'{b.name}: head={b.head_local}')
"""
Path("tools/blitzwing/inspect_source_feet_bones.py").write_text(script, encoding="utf-8")
