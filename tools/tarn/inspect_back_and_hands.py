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

# Check Armature.000 & Armature.001 bone rest vs pose matrices & vertex group bounds
for aname, mname in [("Armature.000", "Cylinder.001"), ("Armature.001", "Cylinder.002")]:
    arm = bpy.data.objects[aname]
    mobj = bpy.data.objects[mname]
    print(f"=== {aname} / {mname} ===")
    print(f"  arm det={arm.matrix_world.to_3x3().determinant():.3f}, mesh det={mobj.matrix_world.to_3x3().determinant():.3f}")
    # Check pose bone rotation offsets
    posed_bones = []
    for pb in arm.pose.bones:
        if pb.rotation_quaternion != mathutils.Quaternion((1,0,0,0)) or pb.location.length > 1e-4:
            posed_bones.append((pb.name, tuple(round(x,3) for x in pb.rotation_quaternion)))
    print(f"  Posed bones count={len(posed_bones)}: {posed_bones[:8]}")

# Render untouched back view (+Y looking to -Y)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1200
scene.render.resolution_y = 1200
if not scene.world:
    scene.world = bpy.data.worlds.new("W")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.19, 0.23, 1.0)
scene.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

for l in [o for o in bpy.data.objects if o.type == 'LIGHT']:
    bpy.data.objects.remove(l, do_unlink=True)

def look_at(obj, pos, target):
    obj.location = mathutils.Vector(pos)
    obj.rotation_euler = (mathutils.Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()

tgt = (-33.65, 1.0, -31.0)
for nm, pos, en in [("Key", (-10, 90, 20), 3.0), ("Fill", (-70, 90, -10), 1.8), ("Rim", (-34, -60, 0), 2.5)]:
    lo = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN'))
    lo.data.energy = en
    scene.collection.objects.link(lo)
    look_at(lo, pos, tgt)

cam = bpy.data.objects.new("SrcCamBack", bpy.data.cameras.new("SrcCamBack"))
cam.data.lens = 45.0
scene.collection.objects.link(cam)
scene.camera = cam

look_at(cam, (-33.65, 130.0, -31.0), tgt)
scene.render.filepath = str(SCRATCH_DIR / "src_untouched_back_posY.png")
bpy.ops.render.render(write_still=True)

# Also render closeup of Cube.049 & Cylinder.045 isolated so we see what they actually are!
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = o.name not in ("Cube.049", "Cylinder.045", "Cube.030", "Cube.045")
look_at(cam, (-33.65, -80.0, -48.0), (-33.65, 2.0, -48.0))
scene.render.filepath = str(SCRATCH_DIR / "src_cube049_cyl045.png")
bpy.ops.render.render(write_still=True)
print("[OK] Rendered untouched back & Cube.049/Cyl.045!")
