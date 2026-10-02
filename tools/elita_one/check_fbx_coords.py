import bpy
import bmesh
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

obj = bpy.data.objects.get("SK_CH_11.001")
mesh = obj.data

# Let's inspect vertices that have high Z (> 6.0) or are near the floating cubes
# In the FBX coordinates, what is the bounding box of SK_CH_11.001?
print(f"Bounding box: {obj.dimensions}")
print(f"Min/Max coords:")
min_x = min(v.co.x for v in mesh.vertices)
max_x = max(v.co.x for v in mesh.vertices)
min_y = min(v.co.y for v in mesh.vertices)
max_y = max(v.co.y for v in mesh.vertices)
min_z = min(v.co.z for v in mesh.vertices)
max_z = max(v.co.z for v in mesh.vertices)
print(f"X: [{min_x:.3f}, {max_x:.3f}], Y: [{min_y:.3f}, {max_y:.3f}], Z: [{min_z:.3f}, {max_z:.3f}]")

# Now check the vertex groups of vertices in the blend file when animated
