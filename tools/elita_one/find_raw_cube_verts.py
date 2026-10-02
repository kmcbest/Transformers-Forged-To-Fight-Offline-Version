import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

obj = bpy.data.objects.get("SK_CH_11.001")
mesh = obj.data

# Let's find vertices that were in Component 0 of find_cubes.py
# In find_cubes.py, Component 0 had original center in elita_mesh of:
# (-0.0002, 0.6772, 8.2534).
# In elita_mesh:
# elita_mesh coords = rot_z_90(raw * 1.094)
# so raw_x = y / 1.094 = 0.6772 / 1.094 = 0.619
# raw_y = -x / 1.094 = 0.0002 / 1.094 = 0.000
# raw_z = 8.2534 / 1.094 = 7.544
# Let's search raw mesh vertices near (0.619, 0.0, 7.544):

matches = []
for i, v in enumerate(mesh.vertices):
    if abs(v.co.x - 0.619) < 0.05 and abs(v.co.y) < 0.05 and abs(v.co.z - 7.544) < 0.05:
        matches.append(i)

print(f"Found {len(matches)} matching vertices in raw FBX: {matches}")
for idx in matches[:5]:
    v = mesh.vertices[idx]
    vgs = [(obj.vertex_groups[g.group].name, g.weight) for g in v.groups]
    # find polygons sharing this vertex
    polys = [p.index for p in mesh.polygons if idx in p.vertices]
    print(f"Vert {idx}: co={v.co}, groups={vgs}, polys={polys}")
