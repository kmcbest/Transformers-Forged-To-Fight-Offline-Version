import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
import mathutils
from pathlib import Path

# Open fresh FBX
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\vortex_prepared.fbx")

# Check vertices belonging to IonBlade
mesh = bpy.data.objects["cha_vortex_gs_00"]
# Polygons with material index matching weapon (slot 0 has M_Vortex_Main, let's find blade polygons)
# The blade was appended at the end: verts 11706 to 17374
# Let's check coordinates of the blade vertices
blade_l_indices = list(range(11706, 11706 + 2834))
blade_r_indices = list(range(11706 + 2834, 17374))

zs_l = [mesh.data.vertices[i].co.z for i in blade_l_indices]
print(f"Current Blade_L Z range: [{min(zs_l):.3f}, {max(zs_l):.3f}]")

# Wrist is at Z ~ 5.75. If we rotate the blade around the wrist mount point (Z=5.75, Y=0.0):
# A forward tilt (around X) of 30-40 degrees brings the tip forward and UP!
# Or scaling by 0.75 brings the length from 6.0m to 4.5m!
