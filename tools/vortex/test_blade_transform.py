import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
import mathutils
from pathlib import Path

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vortex_master.blend")
arm = bpy.data.objects["Vortex_ARM"]
blade_l = bpy.data.objects["WEP_IonBlade_SKEL.mo_L.dmx"]
blade_r = bpy.data.objects["WEP_IonBlade_SKEL.mo_R.dmx"]

scale_factor = 2.05
arm.scale = (scale_factor, scale_factor, scale_factor)
arm.rotation_euler = (0, 0, math.radians(90.0))
bpy.context.view_layer.update()

# Pose Left arm downwards to test blade position
# When arm modifier is applied on blade, let's see where the blade ends up
# If we scale the blade mesh data around its hilt:
# Let's check hilt center in blade local coordinates:
# Raw blade bounds: X=[-0.450, 0.888], Y=[1.789, 4.398], Z=[0.444, 3.409]
# Hilt is near Y=2.32 (wrist bone)
for side, blade_obj in [("L", blade_l), ("R", blade_r)]:
    # In local mesh coordinates before armature bake:
    # Scale blade by 0.70 along length, and tilt slightly forward
    pass
