import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'stderr'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

SRC = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Blitzwing_EW\01_source\H_shandian_G1_M_LOD.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC))

mesh = bpy.data.objects['H_shandian_G1_M_Lod']
vgs = {vg.index: vg.name for vg in mesh.vertex_groups}

# Check overlap between Finger2 and Finger3
vg_f2 = mesh.vertex_groups['Bip001 L Finger2'].index
vg_f3 = mesh.vertex_groups['Bip001 L Finger3'].index

f2_v = {v.index for v in mesh.data.vertices for g in v.groups if g.group == vg_f2 and g.weight > 0.01}
f3_v = {v.index for v in mesh.data.vertices for g in v.groups if g.group == vg_f3 and g.weight > 0.01}

print(f"F2 count: {len(f2_v)}, F3 count: {len(f3_v)}, Intersection: {len(f2_v & f3_v)}")
