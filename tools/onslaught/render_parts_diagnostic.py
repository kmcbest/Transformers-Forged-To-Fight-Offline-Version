import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import math
from pathlib import Path
import bpy
import mathutils

MASTER_BLEND = Path(r"E:\Agent\TFTF-blender\3rd-party-models\onslaught\onslaught_master.blend")
OUT_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch")
OUT_DIR.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(MASTER_BLEND))

# Setup clean studio world & lights & camera
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.film_transparent = False

if not scene.world:
    scene.world = bpy.data.worlds.new("StudioWorld")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.16, 0.17, 0.20, 1.0)
    bg.inputs[1].default_value = 1.0

# Clear existing cameras/lights
for o in list(bpy.data.objects):
    if o.type in ('CAMERA', 'LIGHT'):
        bpy.data.objects.remove(o, do_unlink=True)

# Note: In master blend, Onslaught faces +X, Left is +Y, Up is +Z!
# Center of Onslaught is roughly (0, 0, 3.0), height 6.04m, width Y [-4.3, 4.3]
cam_data = bpy.data.cameras.new("DiagCam")
cam_data.lens = 35
cam_obj = bpy.data.objects.new("DiagCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

def look_at(obj, pos, target):
    obj.location = mathutils.Vector(pos)
    direction = mathutils.Vector(target) - obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    obj.rotation_euler = rot_quat.to_euler()

for name, pos, energy in [
    ("KeyLight", (8.0, -5.0, 7.0), 4.0),
    ("FillLight", (6.0, 6.0, 4.0), 2.5),
    ("BackLight", (-8.0, 0.0, 6.0), 3.0),
]:
    ld = bpy.data.lights.new(name, type='SUN')
    ld.energy = energy
    lo = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(lo)
    look_at(lo, pos, (0, 0, 3.0))

body_parts = {
    "RB_Onslaught_CHARSKEL_Chest.mo.dmx",
    "RB_Onslaught_CHARSKEL_Legs.mo.dmx",
    "RB_Onslaught_CHARSKEL_Head.mo.dmx",
    "RB_Onslaught_CHARSKEL_ArmLoL.mo.dmx",
    "RB_Onslaught_CHARSKEL_ArmLoR.mo.dmx",
    "RB_Onslaught_CHARSKEL_CapL.mo.dmx",
    "RB_Onslaught_CHARSKEL_CapR.mo.dmx",
    "RB_Onslaught_STAT_Wheel.mo.005.dmx",
    "RB_Onslaught_STAT_Wheel.mo.006.dmx",
    "RB_Onslaught_STAT_Wheel.mo.007.dmx",
    "RB_Onslaught_STAT_Wheel.mo.008.dmx",
}
rl_parts = {"RB_RocketLauncherL_SKEL.mo.dmx", "RB_RocketLauncherR_SKEL.mo.dmx"}
hmg_parts = {"RB_HeavyMGL_SKEL.mo.dmx", "RB_HeavyMGR_SKEL.mo.dmx"}
arm_lo_parts = {"RB_Onslaught_CHARSKEL_ArmLoL.mo.dmx", "RB_Onslaught_CHARSKEL_ArmLoR.mo.dmx"}

def set_vis(visible_set):
    for o in bpy.data.objects:
        if o.type == 'MESH':
            hide = o.name not in visible_set
            o.hide_render = hide
            o.hide_viewport = hide

# 1. Pure Robot (Normal Arms, Front-3Q and Back-3Q)
set_vis(body_parts)
look_at(cam_obj, (8.5, -4.0, 3.4), (0.0, 0.0, 3.0))
scene.render.filepath = str(OUT_DIR / "diag_01_robot_normal_arms_front.png")
bpy.ops.render.render(write_still=True)

look_at(cam_obj, (-8.5, 4.0, 3.6), (0.0, 0.0, 3.0))
scene.render.filepath = str(OUT_DIR / "diag_02_robot_normal_arms_back.png")
bpy.ops.render.render(write_still=True)

# 2. Robot with RocketLauncher arms (replacing ArmLoL/R!)
set_vis((body_parts - arm_lo_parts) | rl_parts)
look_at(cam_obj, (9.0, -4.5, 3.4), (0.0, 0.0, 3.0))
scene.render.filepath = str(OUT_DIR / "diag_03_robot_rocket_arms.png")
bpy.ops.render.render(write_still=True)

# 3. Robot with HeavyMG arms (replacing ArmLoL/R!)
set_vis((body_parts - arm_lo_parts) | hmg_parts)
look_at(cam_obj, (9.0, -4.5, 3.4), (0.0, 0.0, 3.0))
scene.render.filepath = str(OUT_DIR / "diag_04_robot_heavymg_arms.png")
bpy.ops.render.render(write_still=True)

# 4. Also check what happens when ArmLoR + RocketLauncherL or HeavyMG is combined, or check weapon subparts
print("[✓] Rendered all 4 diagnostic views!")
