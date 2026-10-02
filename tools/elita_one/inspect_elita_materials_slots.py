import sys
import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
BLEND_FILE = ROOT / "tools" / "elita_one" / "elita_one_arcee_side_by_side.blend"

bpy.ops.wm.open_mainfile(filepath=str(BLEND_FILE))
elita_mesh = bpy.data.objects.get("Elita_One_Mesh")

print(f"Elita_One_Mesh materials: {[m.name for m in elita_mesh.data.materials]}")
counts = {}
for p in elita_mesh.data.polygons:
    counts[p.material_index] = counts.get(p.material_index, 0) + 1

print(f"Polygon counts per material slot: {counts}")
