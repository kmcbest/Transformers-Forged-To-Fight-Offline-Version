import sys
from pathlib import Path
import bpy

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
fbx_path = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Blitzwing" / "blitzwing_robot.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

mesh = [o for o in bpy.data.objects if o.type == 'MESH'][0]
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]

print(f"Total verts: {len(zs)}")
print(f"Min Z: {min(zs)}, Max Z: {max(zs)}")

# Print the top 5 lowest vertices
sorted_indices = sorted(range(len(zs)), key=lambda i: zs[i])
for i in sorted_indices[:10]:
    v = mesh.data.vertices[i]
    print(f"  Vert {i}: co={v.co}, groups={[ (g.group, g.weight) for g in v.groups ]}")
