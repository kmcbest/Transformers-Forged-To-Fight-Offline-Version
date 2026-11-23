import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
from mathutils import Vector, Matrix

# 1. Measure exact Blitzwing LeftHand and RightHand world geometry and convert to UNITY RightHand/LeftHand bone space!
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\Blitzwing_EW\03_fbx_exports\cha_blitzwing_gs_00_robot.fbx")
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
bpy.context.view_layer.update()

print("=== Blender Armature Hand Bone Matrices ===")
for bn in ("LeftHand", "RightHand"):
    M = arm.matrix_world @ arm.pose.bones[bn].matrix
    print(f"  {bn}: pos={tuple(round(v,4) for v in M.translation)}")
    for r in range(3):
        print("   ", [round(M[r][c], 4) for c in range(4)])

# Convert Blitzwing Robot vertices weighted to LeftHand / RightHand into UNITY hand local space!
# Unity World Coords: u = (-x_b, z_b, -y_b)
# Unity LeftHand world origin = (-2.4734, 5.5272, -0.0470), basis: X_u=(0,1,0), Y_u=(-1,0,0), Z_u=(0,0,1)
# Unity RightHand world origin = (+2.4734, 5.5272, -0.0470), basis: X_u=(0,1,0), Y_u=(-1,0,0), Z_u=(0,0,1)
def to_unity_hand(v_b, hand_origin_u):
    u = Vector((-v_b.x, v_b.z, -v_b.y)) - hand_origin_u
    # Since Unity Hand basis has X_h = (0,1,0), Y_h = (-1,0,0), Z_h = (0,0,1):
    return Vector((u.y, -u.x, u.z))

lh_origin_u = Vector((-2.4734, 5.5272, -0.0470))
rh_origin_u = Vector((+2.4734, 5.5272, -0.0470))

for bn, orig_u in [("LeftHand", lh_origin_u), ("RightHand", rh_origin_u)]:
    vg_idx = mesh.vertex_groups[bn].index
    pts = []
    for v in mesh.data.vertices:
        w = sum(g.weight for g in v.groups if g.group == vg_idx)
        if w > 0.5:
            pw = mesh.matrix_world @ v.co
            pts.append(to_unity_hand(pw, orig_u))
    # Fist region (below wrist, x < -0.35 in Unity hand space)
    fist = [p for p in pts if p.x < -0.35]
    c_all = sum(pts, Vector((0,0,0))) / len(pts)
    c_fist = sum(fist, Vector((0,0,0))) / len(fist)
    print(f"\n=== Blitzwing {bn} in UNITY {bn} local space ===")
    print(f"  All bbox:  X=[{min(p.x for p in pts):.3f}, {max(p.x for p in pts):.3f}], Y=[{min(p.y for p in pts):.3f}, {max(p.y for p in pts):.3f}], Z=[{min(p.z for p in pts):.3f}, {max(p.z for p in pts):.3f}]")
    print(f"  Fist bbox: X=[{min(p.x for p in fist):.3f}, {max(p.x for p in fist):.3f}], Y=[{min(p.y for p in fist):.3f}, {max(p.y for p in fist):.3f}], Z=[{min(p.z for p in fist):.3f}, {max(p.z for p in fist):.3f}]")
    print(f"  Fist center in UNITY {bn}: {tuple(round(v, 4) for v in c_fist)}")

# 2. Inspect EW source weapons in H_shandian_G1_M_LOD.fbx
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\Blitzwing_EW\01_source\H_shandian_G1_M_LOD.fbx")
bpy.context.view_layer.update()
for nm in ("H_shandian_G1_W1_Lod", "H_shandian_G1_W2_Lod"):
    obj = bpy.data.objects.get(nm)
    pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    print(f"\n=== EW {nm} (verts={len(pts)}) ===")
    print(f"  World bbox: X=[{min(p.x for p in pts):.5f}, {max(p.x for p in pts):.5f}], Y=[{min(p.y for p in pts):.5f}, {max(p.y for p in pts):.5f}], Z=[{min(p.z for p in pts):.5f}, {max(p.z for p in pts):.5f}]")
    # Slice handle region for Sword (Z < 0.011) & Gun grip (X in [-0.011, 0.002], Z < 0.013)
    if "W1" in nm:
        handle = [p for p in pts if p.z < 0.010]
        print(f"  Sword handle (Z<0.010) center: X={sum(p.x for p in handle)/len(handle):.5f}, Y={sum(p.y for p in handle)/len(handle):.5f}, Z=[{min(p.z for p in handle):.5f}, {max(p.z for p in handle):.5f}]")
        blade = [p for p in pts if p.z > 0.012]
        print(f"  Sword blade  (Z>0.012): X=[{min(p.x for p in blade):.5f}, {max(p.x for p in blade):.5f}], Y=[{min(p.y for p in blade):.5f}, {max(p.y for p in blade):.5f}], Z=[{min(p.z for p in blade):.5f}, {max(p.z for p in blade):.5f}]")
    else:
        grip = [p for p in pts if p.z < 0.0115 and -0.010 < p.x < 0.002]
        if grip:
            print(f"  Gun grip (Z<0.0115, -0.01<X<0.002): cnt={len(grip)} X={sum(p.x for p in grip)/len(grip):.5f} [{min(p.x for p in grip):.5f},{max(p.x for p in grip):.5f}], Y={sum(p.y for p in grip)/len(grip):.5f} [{min(p.y for p in grip):.5f},{max(p.y for p in grip):.5f}], Z=[{min(p.z for p in grip):.5f},{max(p.z for p in grip):.5f}]")
