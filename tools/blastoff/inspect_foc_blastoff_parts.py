import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

BLASTOFF_MESH_NAMES = [
    "RB_Blastoff_CHARSKEL_Head.001.dmx",
    "RB_Blastoff_CHARSKEL_ArmLoL.001.dmx",
    "RB_Blastoff_CHARSKEL_ArmLoR.001.dmx",
    "RB_BlastoffWing_STAT.001.dmx",
    "RB_BlastoffWing_STAT.dmx",
]

for name in BLASTOFF_MESH_NAMES:
    o = bpy.data.objects.get(name)
    if o:
        mats = [s.material.name if s.material else "" for s in o.material_slots]
        print(f"Object: {name} (verts={len(o.data.vertices)})")
        print(f"  Materials: {mats}")
        vg_names = [vg.name for vg in o.vertex_groups]
        foot_vgs = [vg for vg in vg_names if any(k in vg.lower() for k in ("foot", "toe", "leg", "hip"))]
        print(f"  Leg/Foot VGs: {foot_vgs}")
