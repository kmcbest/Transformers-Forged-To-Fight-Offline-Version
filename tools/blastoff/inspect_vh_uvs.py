import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

target_names = [
    "VH_Blastoff_SKEL.mo.dmx",
    "VH_BlastoffWing_STAT.mo.001.dmx",
    "VH_BlastoffWing_STAT.mo.dmx",
]

for name in target_names:
    o = bpy.data.objects.get(name)
    if not o:
        continue
    uvl = o.data.uv_layers.active
    mat_slots = [s.name for s in o.material_slots]
    print(f"\nObject: {name}")
    for mat_idx, mname in enumerate(mat_slots):
        poly_indices = [p for p in o.data.polygons if p.material_index == mat_idx]
        us, vs = [], []
        for p in poly_indices:
            for li in p.loop_indices:
                uv = uvl.data[li].uv
                us.append(uv.x)
                vs.append(uv.y)
        if us:
            print(f"  Material [{mname}]: count={len(poly_indices)} polys, U=[{min(us):.3f}, {max(us):.3f}], V=[{min(vs):.3f}, {max(vs):.3f}]")
