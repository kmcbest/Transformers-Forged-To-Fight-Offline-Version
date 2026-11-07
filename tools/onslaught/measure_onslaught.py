import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

master_blend = Path(r"E:\Agent\TFTF-blender\3rd-party-models\onslaught\onslaught_master.blend")
bpy.ops.wm.open_mainfile(filepath=str(master_blend))

# Get all robot meshes
robot_mesh_names = [
    "RB_Onslaught_CHARSKEL_ArmLoL.mo.dmx",
    "RB_Onslaught_CHARSKEL_ArmLoR.mo.dmx",
    "RB_Onslaught_CHARSKEL_CapL.mo.dmx",
    "RB_Onslaught_CHARSKEL_CapR.mo.dmx",
    "RB_Onslaught_CHARSKEL_Chest.mo.dmx",
    "RB_Onslaught_CHARSKEL_Head.mo.dmx",
    "RB_Onslaught_CHARSKEL_Legs.mo.dmx",
    "RB_Onslaught_STAT_Wheel.mo.005.dmx",
    "RB_Onslaught_STAT_Wheel.mo.006.dmx",
    "RB_Onslaught_STAT_Wheel.mo.007.dmx",
    "RB_Onslaught_STAT_Wheel.mo.008.dmx",
    "RB_HeavyMGL_SKEL.mo.dmx",
    "RB_HeavyMGR_SKEL.mo.dmx",
    "RB_RocketLauncherL_SKEL.mo.dmx",
    "RB_RocketLauncherR_SKEL.mo.dmx"
]

all_pts = []
for name in robot_mesh_names:
    o = bpy.data.objects.get(name)
    if o:
        for v in o.data.vertices:
            all_pts.append(o.matrix_world @ v.co)

min_x = min(p.x for p in all_pts)
max_x = max(p.x for p in all_pts)
min_y = min(p.y for p in all_pts)
max_y = max(p.y for p in all_pts)
min_z = min(p.z for p in all_pts)
max_z = max(p.z for p in all_pts)

print(f"=== ONSLAUGHT BOUNDS IN BLENDER ===")
print(f"X (depth): [{min_x:.3f}, {max_x:.3f}] -> size: {max_x - min_x:.3f}m")
print(f"Y (width): [{min_y:.3f}, {max_y:.3f}] -> size: {max_y - min_y:.3f}m")
print(f"Z (height): [{min_z:.3f}, {max_z:.3f}] -> size: {max_z - min_z:.3f}m")

# Check without back cannons (just body)
body_pts = []
for name in robot_mesh_names[:11]:
    o = bpy.data.objects.get(name)
    if o:
        for v in o.data.vertices:
            body_pts.append(o.matrix_world @ v.co)

b_min_z = min(p.z for p in body_pts)
b_max_z = max(p.z for p in body_pts)
print(f"\nBody-only height: {b_max_z - b_min_z:.3f}m (from Z={b_min_z:.3f} to Z={b_max_z:.3f})")
