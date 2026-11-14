import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
import mathutils

TARN_ROOT = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn")
CLEANED_BLEND = TARN_ROOT / "06_working" / "tarn_workspace_cleaned.blend"
SRC_BLEND = TARN_ROOT / "01_robot_source" / "source" / "last comp3.blend"
SCRATCH_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\66aaeff3-2652-4f24-8fc9-00b0ef375582\scratch")
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

print("=== 1. Inspecting Original last comp3.blend ===")
bpy.ops.wm.open_mainfile(filepath=str(SRC_BLEND))

for arm in bpy.data.armatures:
    print(f"Armature: {arm.name} | bones={len(arm.bones)} | names={[b.name for b in arm.bones[:15]]}")

for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        print(f"Armature Obj: {o.name} loc={tuple(round(x,3) for x in o.location)} scale={tuple(round(x,3) for x in o.scale)} children={[c.name for c in o.children]}")

print("\nMeshes with Armature modifiers or vertex groups in last comp3.blend:")
for o in bpy.data.objects:
    if o.type == 'MESH':
        mods = [f"{m.type}({m.show_viewport}/{m.show_render})" for m in o.modifiers]
        vgs = [vg.name for vg in o.vertex_groups]
        mats = [ms.material.name for ms in o.material_slots if ms.material]
        if vgs or any("ARMATURE" in m for m in mods) or len(o.data.vertices) > 5000:
            wmin = [min((o.matrix_world @ v.co)[i] for v in o.data.vertices) for i in range(3)]
            wmax = [max((o.matrix_world @ v.co)[i] for v in o.data.vertices) for i in range(3)]
            print(f"  {o.name:18s} | verts={len(o.data.vertices):6d} | polys={len(o.data.polygons):6d} | mods={mods} | vgs={len(vgs)} {vgs[:4]} | mats={mats} | bbox_min={tuple(round(x,2) for x in wmin)} bbox_max={tuple(round(x,2) for x in wmax)}")

# Check overall bounding box of all meshes in source blend
all_pts = []
for o in bpy.data.objects:
    if o.type == 'MESH':
        for v in o.data.vertices:
            all_pts.append(o.matrix_world @ v.co)
s_min = [min(p[i] for p in all_pts) for i in range(3)]
s_max = [max(p[i] for p in all_pts) for i in range(3)]
print(f"\nSource overall mesh bounds: min={tuple(round(x,2) for x in s_min)}, max={tuple(round(x,2) for x in s_max)}")

print("\n=== 2. Inspecting Cleaned Workspace ===")
bpy.ops.wm.open_mainfile(filepath=str(CLEANED_BLEND))

for img in bpy.data.images:
    print(f"  Image: {img.name:35s} | src={img.source:9s} | size={img.size[0]}x{img.size[1]} | has_data={img.has_data} | packed={img.packed_file is not None} | path={img.filepath}")

def bbox_info(obj):
    pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    mn = [min(p[i] for p in pts) for i in range(3)]
    mx = [max(p[i] for p in pts) for i in range(3)]
    return mn, mx

for name in ["Tarn_Robot_LowPoly", "REF_cha_megatron_gs_leader2015_00_robot", "REF_cha_megatron_gs_leader2015_01_tank", "REF_cha_megatron_gs_leader2015_wpns_cannon_right"]:
    o = bpy.data.objects.get(name)
    if o and o.type == 'MESH':
        mn, mx = bbox_info(o)
        tris = sum(max(0, len(p.vertices)-2) for p in o.data.polygons)
        print(f"  {name:42s}: verts={len(o.data.vertices):6d}, tris={tris:6d}, min={tuple(round(x,3) for x in mn)}, max={tuple(round(x,3) for x in mx)}")

print("\nVehicle objects:")
for o in bpy.data.objects:
    if o.type == 'MESH' and ("TarnTank" in o.name or "Vehicle" in o.name):
        mn, mx = bbox_info(o)
        tris = sum(max(0, len(p.vertices)-2) for p in o.data.polygons)
        vgs = [vg.name for vg in o.vertex_groups]
        print(f"  {o.name:28s}: verts={len(o.data.vertices):5d}, tris={tris:5d}, vgs={len(vgs)} {vgs[:4]}, min={tuple(round(x,3) for x in mn)}, max={tuple(round(x,3) for x in mx)}")

# Inspect part__ vertex groups by triangle count in Tarn_Robot_LowPoly
rob = bpy.data.objects.get("Tarn_Robot_LowPoly")
if rob:
    vg_verts = {vg.index: 0 for vg in rob.vertex_groups}
    for v in rob.data.vertices:
        for g in v.groups:
            vg_verts[g.group] += 1
    top_parts = sorted(((rob.vertex_groups[k].name, cnt) for k, cnt in vg_verts.items()), key=lambda x: -x[1])
    print("\nTop 25 parts by vertex count in Tarn_Robot_LowPoly:")
    for nm, cnt in top_parts[:25]:
        print(f"  {nm:30s}: {cnt:6d} verts")

# Render Gate 1 Preview (Tarn_Robot_LowPoly vs REF_00, plus Vehicle vs REF_01) using EEVEE material preview
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
if not scene.world:
    scene.world = bpy.data.worlds.new("W")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.19, 0.23, 1.0)
scene.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

# Clear old lights and add studio lights
for l in [o for o in bpy.data.objects if o.type == 'LIGHT']:
    bpy.data.objects.remove(l, do_unlink=True)

def look_at(obj, pos, target):
    obj.location = mathutils.Vector(pos)
    obj.rotation_euler = (mathutils.Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()

for nm, pos, en in [("Key", (8, -18, 14), 3.0), ("Fill", (-10, -15, 8), 1.8), ("Rim", (0, 18, 12), 2.5)]:
    lo = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN'))
    lo.data.energy = en
    scene.collection.objects.link(lo)
    look_at(lo, pos, (0, 0, 5.5))

cam = bpy.data.objects.new("DiagCam", bpy.data.cameras.new("DiagCam"))
cam.data.lens = 45.0
scene.collection.objects.link(cam)
scene.camera = cam

# Hide vehicle and ref_tank while rendering robot views
for o in bpy.data.objects:
    if "TarnTank" in o.name or "01_tank" in o.name or "cannon_right" in o.name:
        o.hide_render = True

# Move REF_00 to X = +6.5 so we can compare side by side
ref0 = bpy.data.objects.get("REF_cha_megatron_gs_leader2015_00_robot")
if ref0:
    ref0.location = (6.5, 0, 0)
    ref0.hide_render = False

if rob:
    rob.hide_render = False
    rob.location = (0, 0, 0)

for vname, cpos, ctgt in [
    ("gate1_robot_front.png", (3.2, -24.0, 5.8), (3.2, 0.0, 5.6)),
    ("gate1_robot_back.png", (0.0, 22.0, 6.0), (0.0, 0.0, 5.6)),
    ("gate1_robot_side_L.png", (-22.0, -2.0, 5.8), (0.0, 0.0, 5.6)),
]:
    look_at(cam, cpos, ctgt)
    scene.render.filepath = str(SCRATCH_DIR / vname)
    bpy.ops.render.render(write_still=True)

# Now hide robot and render vehicle vs REF_01_tank
if rob:
    rob.hide_render = True
if ref0:
    ref0.hide_render = True
for o in bpy.data.objects:
    if "TarnTank" in o.name or "01_tank" in o.name:
        o.hide_render = False

ref1 = bpy.data.objects.get("REF_cha_megatron_gs_leader2015_01_tank")
if ref1:
    ref1.location = (8.5, 0, 0)

look_at(cam, (4.2, -16.0, 8.0), (4.2, 0.0, 0.5))
scene.render.filepath = str(SCRATCH_DIR / "gate1_vehicle_sbs.png")
bpy.ops.render.render(write_still=True)
print("[OK] Diagnostic renders saved to", SCRATCH_DIR)
