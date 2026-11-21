import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
import numpy as np

ROBOT_FBX = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=ROBOT_FBX)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
all_co = []
for m in meshes:
    for v in m.data.vertices:
        w_co = m.matrix_world @ v.co
        all_co.append([w_co.x, w_co.y, w_co.z])

co = np.array(all_co)
print(f"Raw world coords: min={co.min(axis=0)}, max={co.max(axis=0)}")
# co[:, 0] is X, co[:, 1] is Y (Up), co[:, 2] is Z (Fwd/Back)

# Transform: X_b = X, Y_b = -Z, Z_b = Y
b_co = np.stack([co[:, 0], -co[:, 2], co[:, 1]], axis=1)
print(f"Blender raw coords: min={b_co.min(axis=0)}, max={b_co.max(axis=0)}")

# Ground feet at Z=0
z_min = b_co[:, 2].min()
b_co[:, 2] -= z_min
height_raw = b_co[:, 2].max()
print(f"Grounded height raw = {height_raw:.4f}")

# Target height: Barricade is ~10.85m tall.
# Let's scale to 10.85m:
scale = 10.85 / height_raw
b_co_scaled = b_co * scale
print(f"Scaled by {scale:.2f}:")
print(f"  X (width): [{b_co_scaled[:, 0].min():.3f}, {b_co_scaled[:, 0].max():.3f}] (width={b_co_scaled[:, 0].max() - b_co_scaled[:, 0].min():.3f})")
print(f"  Y (depth): [{b_co_scaled[:, 1].min():.3f}, {b_co_scaled[:, 1].max():.3f}] (depth={b_co_scaled[:, 1].max() - b_co_scaled[:, 1].min():.3f})")
print(f"  Z (height): [{b_co_scaled[:, 2].min():.3f}, {b_co_scaled[:, 2].max():.3f}] (height={b_co_scaled[:, 2].max():.3f})")
