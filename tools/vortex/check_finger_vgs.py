import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vortex_master.blend")
armlo_l = bpy.data.objects["RB_Vortex_CHARSKEL_ArmLoL.mo.dmx"]

for fn in ["index", "middle", "ring", "pinky", "thumb"]:
    vg0 = armlo_l.vertex_groups.get(f"bip_{fn}_0_L")
    vg1 = armlo_l.vertex_groups.get(f"bip_{fn}_1_L")
    c0 = sum(1 for v in armlo_l.data.vertices if any(g.group == vg0.index and g.weight > 0.5 for g in v.groups)) if vg0 else 0
    c1 = sum(1 for v in armlo_l.data.vertices if any(g.group == vg1.index and g.weight > 0.5 for g in v.groups)) if vg1 else 0
    print(f"Finger {fn:7s}: vg0={c0} verts, vg1={c1} verts")
