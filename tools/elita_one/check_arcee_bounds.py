import json
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
ARCEE_FULL_MESH = ROOT / "tools" / "elita_one" / "arcee_full_mesh.json"

with open(ARCEE_FULL_MESH, "r") as f:
    data = json.load(f)

verts = data["vertices"]
xs = [v["x"] for v in verts]
ys = [v["z"] for v in verts] # Note: in Blender, y_b = z_u
zs = [v["y"] for v in verts] # z_b = y_u

print(f"Arcee Mesh Bounds in Blender coords:")
print(f"X: [{min(xs):.3f}, {max(xs):.3f}] (width: {max(xs)-min(xs):.3f})")
print(f"Y: [{min(ys):.3f}, {max(ys):.3f}] (depth: {max(ys)-min(ys):.3f})")
print(f"Z: [{min(zs):.3f}, {max(zs):.3f}] (height: {max(zs)-min(zs):.3f})")
