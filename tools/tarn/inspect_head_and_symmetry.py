import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
import mathutils

TARN_ROOT = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn")
SRC_BLEND = TARN_ROOT / "01_robot_source" / "source" / "last comp3.blend"
FALLBACK_DIR = TARN_ROOT / "01_robot_source" / "fallback_textures"
SCRATCH_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\66aaeff3-2652-4f24-8fc9-00b0ef375582\scratch")

bpy.ops.wm.open_mainfile(filepath=str(SRC_BLEND))
if FALLBACK_DIR.is_dir():
    bpy.ops.file.find_missing_files(directory=str(FALLBACK_DIR))

print("=== HEAD & POSE SYMMETRY CHECK (around X_sym = -33.65) ===")
head_parts = ["Sphere.001", "Plane.050", "Plane.000", "Cube.008", "Plane.002", "Plane.003", "Sphere.003", "Cube.028", "Torus.000", "Cube.029", "Cylinder.040"]
for nm in head_parts:
    o = bpy.data.objects.get(nm)
    if not o:
        continue
    pts = [o.matrix_world @ v.co for v in o.data.vertices]
    mn = [min(p[i] for p in pts) for i in range(3)]
    mx = [max(p[i] for p in pts) for i in range(3)]
    cx = 0.5*(mn[0]+mx[0]) - (-33.65)
    cy = 0.5*(mn[1]+mx[1])
    cz = 0.5*(mn[2]+mx[2])
    rot_deg = tuple(round(r * 57.2958, 1) for r in o.rotation_euler)
    print(f"  {nm:12s} | dX_from_sym={cx:6.2f} | Y_ctr={cy:6.2f} | Z_ctr={cz:6.2f} | obj_rot_deg={rot_deg} | mats={[ms.material.name for ms in o.material_slots if ms.material]}")

print("\n=== ARM & LEG SYMMETRY CHECK (around X_sym = -33.65) ===")
for nm in ["Cube.020", "Cube.025", "Cube.021", "Cube.006", "Cylinder.001", "Cylinder.002", "Cylinder.038", "Cylinder.062", "Cylinder.003", "Cylinder.004", "Cube.030", "Cube.045"]:
    o = bpy.data.objects.get(nm)
    if not o:
        continue
    pts = [o.matrix_world @ v.co for v in o.data.vertices]
    mn = [min(p[i] for p in pts) for i in range(3)]
    mx = [max(p[i] for p in pts) for i in range(3)]
    cx = 0.5*(mn[0]+mx[0]) - (-33.65)
    cy = 0.5*(mn[1]+mx[1])
    cz = 0.5*(mn[2]+mx[2])
    print(f"  {nm:14s} | dX={cx:6.2f} | Y={cy:6.2f} [{mn[1]:5.1f},{mx[1]:5.1f}] | Z={cz:6.2f} [{mn[2]:5.1f},{mx[2]:5.1f}]")

# Render closer orthographic/front view of head only & hands only
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1000
scene.render.resolution_y = 1000
if not scene.world:
    scene.world = bpy.data.worlds.new("W")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.19, 0.23, 1.0)
for l in [o for o in bpy.data.objects if o.type == 'LIGHT']:
    bpy.data.objects.remove(l, do_unlink=True)
def look_at(obj, pos, target):
    obj.location = mathutils.Vector(pos)
    obj.rotation_euler = (mathutils.Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()
for nm, pos, en in [("Key", (-15, -60, 20), 3.0), ("Fill", (-55, -60, -10), 2.0)]:
    lo = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN'))
    lo.data.energy = en
    scene.collection.objects.link(lo)
    look_at(lo, pos, (-33.65, 0, -4))
cam = bpy.data.objects.new("HeadCam", bpy.data.cameras.new("HeadCam"))
cam.data.lens = 85.0
scene.collection.objects.link(cam)
scene.camera = cam

# Front straight on to head center X=-33.65, Z=-4.0
look_at(cam, (-33.65, -35.0, -4.0), (-33.65, 0.0, -4.0))
scene.render.filepath = str(SCRATCH_DIR / "src_head_straight.png")
bpy.ops.render.render(write_still=True)

# Right hand closeup (Cylinder.002 at X~-52.5, Y~-8.1, Z~-32.1)
look_at(cam, (-52.5, -32.0, -32.5), (-52.5, -8.1, -32.5))
scene.render.filepath = str(SCRATCH_DIR / "src_hand_L_rightarm.png")
bpy.ops.render.render(write_still=True)
