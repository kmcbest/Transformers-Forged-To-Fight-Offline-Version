import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import json
from pathlib import Path

blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vehicle\vortex_vehicle.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))

mesh = bpy.data.objects["VH_Vortex_SKEL.001.dmx"]
arm = bpy.data.objects.get("Vortex_VH_ARM")

xs = [v.co.x for v in mesh.data.vertices]
ys = [v.co.y for v in mesh.data.vertices]
zs = [v.co.z for v in mesh.data.vertices]
print(f"Vortex VH raw bounds: X=[{min(xs):.2f}, {max(xs):.2f}], Y=[{min(ys):.2f}, {max(ys):.2f}], Z=[{min(zs):.2f}, {max(zs):.2f}]")
print(f"Vortex VH mats ({len(mesh.material_slots)}): {[s.material.name if s.material else 'None' for s in mesh.material_slots]}")
print(f"Vortex VH vgs ({len(mesh.vertex_groups)}): {[vg.name for vg in mesh.vertex_groups if 'prop' in vg.name.lower() or 'rotor' in vg.name.lower()]}")

bp_path = Path(r"E:\Agent\TFTF-blender\tools\vortex\grindor_45_vh_authoritative_bindposes.json")
bp_data = json.loads(bp_path.read_text(encoding="utf-8"))
print(f"\nGrindor 45 VH bones ({len(bp_data)}):")
for b, info in bp_data.items():
    if any(k in b.lower() for k in ["rotor", "tail", "body", "wing"]):
        p = info["world_pos"]
        print(f"  {b:22s}: ({p['x']:6.2f}, {p['y']:6.2f}, {p['z']:6.2f})")
