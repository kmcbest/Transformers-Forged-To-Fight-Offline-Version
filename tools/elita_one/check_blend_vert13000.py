import bpy
from pathlib import Path

BLEND = Path(r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend")

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
elita = bpy.data.objects.get("Elita_One_Mesh")
print(f"Total verts in elita: {len(elita.data.vertices)}")
v = elita.data.vertices[13000]
print(f"Vert 13000 in BLEND: co={v.co}")
print(f"Object location={elita.location}, matrix_world=\n{elita.matrix_world}")
