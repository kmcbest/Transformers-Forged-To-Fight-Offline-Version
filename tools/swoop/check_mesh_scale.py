import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FBX_PATH = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

swoop_mesh = bpy.data.objects.get("Swoop.001")
arm = bpy.data.objects.get("Bip001")

print(f"swoop_mesh scale: {swoop_mesh.scale}, loc: {swoop_mesh.location}")
print(f"arm scale: {arm.scale}, loc: {arm.location}")
print(f"swoop_mesh parent: {swoop_mesh.parent}")

# World bounds:
bbox = [swoop_mesh.matrix_world @ Vector(c) for c in swoop_mesh.bound_box]
xs = [v.x for v in bbox]
ys = [v.y for v in bbox]
zs = [v.z for v in bbox]
print(f"WORLD BOUNDS: X=[{min(xs):.3f}, {max(xs):.3f}], Y=[{min(ys):.3f}, {max(ys):.3f}], Z=[{min(zs):.3f}, {max(zs):.3f}]")
