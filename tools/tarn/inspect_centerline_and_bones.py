import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import json
import bpy
import mathutils

TARN_ROOT = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn")
SRC_BLEND = TARN_ROOT / "01_robot_source" / "source" / "last comp3.blend"
DONOR_JSON = TARN_ROOT / "04_donor_reference" / "megatron_gs_leader2015" / "robot_51_bones_and_bindposes.json"
SCRATCH_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\66aaeff3-2652-4f24-8fc9-00b0ef375582\scratch")

# Print Megatron 51 bone positions
spec = json.loads(DONOR_JSON.read_text(encoding='utf-8'))
print("=== MEGATRON GS 51 BONE POSITIONS (Blender space) ===")
for b in spec["bones"]:
    pos = b["blender_pos_matching_obj"]
    print(f"  {b['index']:2d} | {b['name']:22s} | parent={str(b['parent_transform_name']):16s} | ({pos[0]:7.3f}, {pos[1]:7.3f}, {pos[2]:7.3f})")

# Load source blend & inspect centerline + specific parts
bpy.ops.wm.open_mainfile(filepath=str(SRC_BLEND))

# Check mirror modifiers and objects on centerline (X, Y)
print("\n=== SYMMETRIC / CENTERLINE OBJECTS IN SOURCE BLEND ===")
for nm in ["Sphere.001", "Plane.050", "Plane.000", "Cube.008", "Plane.008", "Plane.036", "Cube.019", "Plane.012", "Plane.004", "Plane.018", "Cube.030", "Cube.049", "Cylinder.045", "Cylinder.014"]:
    o = bpy.data.objects.get(nm)
    if not o or o.type != 'MESH':
        continue
    # Evaluate with modifiers (mirror etc)
    deps = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(deps)
    mesh = ev.to_mesh()
    pts = [ev.matrix_world @ v.co for v in mesh.vertices]
    tris = sum(max(0, len(p.vertices)-2) for p in mesh.polygons)
    ev.to_mesh_clear()
    mn = [min(p[i] for p in pts) for i in range(3)]
    mx = [max(p[i] for p in pts) for i in range(3)]
    ctr = [0.5*(mn[i]+mx[i]) for i in range(3)]
    print(f"  {nm:14s}: eval_verts={len(pts):6d} eval_tris={tris:6d} | ctr=({ctr[0]:6.2f}, {ctr[1]:6.2f}, {ctr[2]:6.2f}) | span=({mx[0]-mn[0]:5.2f}, {mx[1]-mn[1]:5.2f}, {mx[2]-mn[2]:5.2f})")

# Check if Hand meshes Cylinder.001 and Cylinder.002 have symmetric mirrors around centerline
for nm in ["Cylinder.001", "Cylinder.002"]:
    o = bpy.data.objects.get(nm)
    deps = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(deps)
    mesh = ev.to_mesh()
    pts = [ev.matrix_world @ v.co for v in mesh.vertices]
    ev.to_mesh_clear()
    mn = [min(p[i] for p in pts) for i in range(3)]
    mx = [max(p[i] for p in pts) for i in range(3)]
    ctr = [0.5*(mn[i]+mx[i]) for i in range(3)]
    print(f"  Hand {nm:12s}: ctr=({ctr[0]:6.2f}, {ctr[1]:6.2f}, {ctr[2]:6.2f}) | min=({mn[0]:6.2f},{mn[1]:6.2f},{mn[2]:6.2f}) max=({mx[0]:6.2f},{mx[1]:6.2f},{mx[2]:6.2f})")
