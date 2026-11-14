import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import json
import bpy
import bmesh
import mathutils

TARN_ROOT = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn")
SRC_BLEND = TARN_ROOT / "01_robot_source" / "source" / "last comp3.blend"
DONOR_OBJ = TARN_ROOT / "04_donor_reference" / "megatron_gs_leader2015" / "cha_megatron_gs_leader2015_01_tank.obj"
TANK_SPEC = TARN_ROOT / "04_donor_reference" / "megatron_gs_leader2015" / "tank_21_bones_and_bindposes.json"
VEH_GLB = TARN_ROOT / "02_vehicle_source" / "Tarn_Vehicle.glb"
SCRATCH_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\66aaeff3-2652-4f24-8fc9-00b0ef375582\scratch")

# 1. Check tank OBJ vertices & tank_21_bones_and_bindposes.json
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(DONOR_OBJ))
ref_tank = [o for o in bpy.data.objects if o.type == 'MESH'][0]
pts = [ref_tank.matrix_world @ v.co for v in ref_tank.data.vertices]
# Check X span at Y < -3 vs Y > +6 (barrel tip is thin!)
neg_y_pts = [p for p in pts if p.y < -4.0]
pos_y_pts = [p for p in pts if p.y > 6.0]
print("=== MEGATRON TANK OBJ AXIS CHECK ===")
print(f"  Overall Y: [{min(p.y for p in pts):.3f}, {max(p.y for p in pts):.3f}]")
print(f"  Y < -4.0 count={len(neg_y_pts)}, X span=[{min(p.x for p in neg_y_pts):.2f}, {max(p.x for p in neg_y_pts):.2f}], Z=[{min(p.z for p in neg_y_pts):.2f}, {max(p.z for p in neg_y_pts):.2f}]")
print(f"  Y > +6.0 count={len(pos_y_pts)}, X span=[{min(p.x for p in pos_y_pts):.2f}, {max(p.x for p in pos_y_pts):.2f}], Z=[{min(p.z for p in pos_y_pts):.2f}, {max(p.z for p in pos_y_pts):.2f}]")

spec = json.loads(TANK_SPEC.read_text(encoding='utf-8'))
print("\n=== TANK 21 BONE POSITIONS ===")
for b in spec["bones"]:
    print(f"  {b['index']:2d} {b['name']:32s} | unity={b['unity_inv_bindpose_pos']} | blender={b['blender_pos_matching_obj']}")

# Import Tarn_Vehicle.glb and check its axis, vertex count after weld, and tread bottom
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(VEH_GLB))
veh_objs = [o for o in (set(bpy.data.objects) - before) if o.type == 'MESH']
print("\n=== TARN VEHICLE GLB CHECK ===")
for o in veh_objs:
    bm = bmesh.new()
    bm.from_mesh(o.data)
    v0 = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0002)
    v1 = len(bm.verts)
    bm.free()
    wpts = [o.matrix_world @ v.co for v in o.data.vertices]
    print(f"  {o.name:25s} | verts={v0:5d} -> weld={v1:5d}, polys={len(o.data.polygons):5d} | Y=[{min(p.y for p in wpts):.2f}, {max(p.y for p in wpts):.2f}], Z=[{min(p.z for p in wpts):.2f}, {max(p.z for p in wpts):.2f}]")

# Check Tarn_Vehicle front vs back (front has twin cannons or plow; back has gold exhausts)
# Wait: look at 02_vehicle_source/renders/01_front.png and gate1_vehicle_sbs.png!
# In gate1_vehicle_sbs.png, camera was at Y=-16 looking +Y, and TarnTank front claw was facing -Y!

# 2. Test clearing pose on Armature.001 (Right Hand) and Armature.000 (Left Hand)
bpy.ops.wm.open_mainfile(filepath=str(SRC_BLEND))
for aname, mname in [("Armature.000", "Cylinder.001"), ("Armature.001", "Cylinder.002")]:
    arm = bpy.data.objects[aname]
    # Keep root Bone orientation, reset all child finger bones (Bone.001..022) to identity pose!
    for pb in arm.pose.bones:
        if pb.name != "Bone":
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.rotation_euler = (0, 0, 0)
            pb.location = (0, 0, 0)
            pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()

# Render both hands side by side in their uncurled rest pose
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1200
scene.render.resolution_y = 600
if not scene.world:
    scene.world = bpy.data.worlds.new("W")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.19, 0.23, 1.0)
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = o.name not in ("Cylinder.001", "Cylinder.002")
    elif o.type == 'LIGHT':
        bpy.data.objects.remove(o, do_unlink=True)
def look_at(obj, pos, target):
    obj.location = mathutils.Vector(pos)
    obj.rotation_euler = (mathutils.Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()
for nm, pos in [("Key", (-34, -80, 0)), ("Rim", (-34, 80, 0))]:
    lo = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN'))
    lo.data.energy = 2.8
    scene.collection.objects.link(lo)
    look_at(lo, pos, (-34, 0, -34))
cam = bpy.data.objects.new("HandCam", bpy.data.cameras.new("HandCam"))
cam.data.lens = 45.0
scene.collection.objects.link(cam)
scene.camera = cam

# Move Cylinder.001 and Cylinder.002? Better move Armatures close together at Y=0, Z=-34 for easy comparison
bpy.data.objects["Armature.000"].location = (-28, 0, -30)
bpy.data.objects["Armature.001"].location = (-40, 0, -30)
bpy.data.objects["Armature.000"].rotation_euler = (0, 0, 0)
bpy.data.objects["Armature.001"].rotation_euler = (0, 0, 0)
# Wait: keep root bone identity too so both hang straight down
for aname in ["Armature.000", "Armature.001"]:
    bpy.data.objects[aname].pose.bones["Bone"].rotation_quaternion = (1, 0, 0, 0)
bpy.context.view_layer.update()
look_at(cam, (-34, -22, -33.5), (-34, 0, -33.5))
scene.render.filepath = str(SCRATCH_DIR / "test_hands_uncurled.png")
bpy.ops.render.render(write_still=True)
print("[OK] Tank axis + uncurled hands test done!")
