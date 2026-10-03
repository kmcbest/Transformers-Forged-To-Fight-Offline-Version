import bpy
from mathutils import Vector, Matrix
from pathlib import Path
import math

ROOT = Path(__file__).resolve().parent.parent.parent
FBX_IN = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"
BLEND_OUT = ROOT / "tools" / "elita_one" / "elita_vehicle_clean.blend"
FBX_OUT = ROOT / "toolchain" / "unity_build_project" / "Assets" / "ElitaOne" / "elita_one_vehicle.fbx"

print(f"=== Extracting Elita One Vehicle Mode ===")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_IN))

# Keep only SK_TR_11.001 (vehicle mesh) and optionally its armature
vh_mesh = bpy.data.objects.get("SK_TR_11.001")
if not vh_mesh:
    raise RuntimeError("Could not find SK_TR_11.001 in FBX!")

# Delete all other objects
for obj in list(bpy.data.objects):
    if obj != vh_mesh:
        bpy.data.objects.remove(obj, do_unlink=True)

# Clear parent if any
vh_mesh.parent = None
vh_mesh.matrix_world = Matrix.Identity(4)

# Current orientation in FBX:
# Front is +X (length 7.41m)
# Left is +Y (width 4.89m)
# Up is +Z (height 2.43m, bottom at Z=0)

# We want Unity/TFTF car standard orientation:
# Forward = +Y in Blender (which exports to +Z in Unity)
# Up = +Z in Blender (which exports to +Y in Unity)
# Right = +X in Blender (which exports to +X in Unity)
# Left = -X in Blender (which exports to -X in Unity)

# In original FBX:
# Front was +X -> needs to become +Y (rotate +90 deg around Z)
# If we rotate by +90 deg around Z:
# Old +X (Front) -> New +Y (Front)
# Old +Y (Left) -> New -X (Left)
# Old -Y (Right) -> New +X (Right)
# Old +Z (Up) -> New +Z (Up)
# This perfectly preserves chirality (right-handed coordinates) without any inversion!

print("[*] Rotating vehicle to standard Forward=+Y, Up=+Z...")
vh_mesh.rotation_euler = (0, 0, math.radians(90))
bpy.context.view_layer.objects.active = vh_mesh
vh_mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Calculate bounding box
bbox = [vh_mesh.matrix_world @ Vector(corner) for corner in vh_mesh.bound_box]
xs = [v.x for v in bbox]
ys = [v.y for v in bbox]
zs = [v.z for v in bbox]

center_x = (min(xs) + max(xs)) / 2.0
center_y = (min(ys) + max(ys)) / 2.0
min_z = min(zs)

print(f"Bbox before center offset:")
print(f"  X (width):  [{min(xs):.3f}, {max(xs):.3f}], center={center_x:.3f}")
print(f"  Y (length): [{min(ys):.3f}, {max(ys):.3f}], center={center_y:.3f}")
print(f"  Z (height): [{min(zs):.3f}, {max(zs):.3f}], min_z={min_z:.3f}")

# Center X and Y around 0, and ensure tires touch ground at Z=0
vh_mesh.location = (-center_x, -center_y, -min_z)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Re-verify bounds
bbox = [vh_mesh.matrix_world @ Vector(corner) for corner in vh_mesh.bound_box]
xs = [v.x for v in bbox]
ys = [v.y for v in bbox]
zs = [v.z for v in bbox]

print(f"\nFinal vehicle dimensions in Blender:")
print(f"  Width  (X): [{min(xs):.3f}, {max(xs):.3f}] (total = {max(xs)-min(xs):.3f}m)")
print(f"  Length (Y): [{min(ys):.3f}, {max(ys):.3f}] (total = {max(ys)-min(ys):.3f}m)")
print(f"  Height (Z): [{min(zs):.3f}, {max(zs):.3f}] (total = {max(zs)-min(zs):.3f}m)")

# Rename mesh
vh_mesh.name = "cha_elita_one_vehicle"
vh_mesh.data.name = "cha_elita_one_vehicle_mesh"

# Save clean .blend
BLEND_OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUT))
print(f"[✓] Saved clean vehicle blend: {BLEND_OUT}")

# Export FBX for Unity (Forward = -Z Forward, Up = Y Up)
FBX_OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.fbx(
    filepath=str(FBX_OUT),
    use_selection=True,
    axis_forward='-Z',
    axis_up='Y',
    apply_scale_options='FBX_SCALE_ALL',
    bake_space_transform=True
)
print(f"[✓] Exported clean vehicle FBX for Unity: {FBX_OUT}")
