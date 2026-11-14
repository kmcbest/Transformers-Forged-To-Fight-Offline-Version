import sys
import json
import numpy as np
import bpy
from mathutils import Vector
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BAKED_BLEND = r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\06_working\tarn_workspace_baked.blend"
UM_BONES_00 = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\04_donor_reference\ultramagnus_gs_leader\cha_ultramagnus_gs_leader_00_bones.json")
UM_OBJ_00 = r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\04_donor_reference\ultramagnus_gs_leader\cha_ultramagnus_gs_leader_00_robot.obj"

bpy.ops.wm.open_mainfile(filepath=BAKED_BLEND)
robot = bpy.data.objects["Tarn_Robot_LowPoly"]

# Import UM OBJ cleanly (default wm.obj_import forward='-Z', up='Y' -> check left vs right hand in Blender!)
bpy.ops.wm.obj_import(filepath=UM_OBJ_00)
um_obj = bpy.context.selected_objects[0]
um_obj.name = "TMP_UM_OBJ"
print(f"Tarn_Robot_LowPoly world bbox: min={tuple(round(min(c[i] for c in [robot.matrix_world @ Vector(b) for b in robot.bound_box]),3) for i in range(3))} max={tuple(round(max(c[i] for c in [robot.matrix_world @ Vector(b) for b in robot.bound_box]),3) for i in range(3))}")

# Check UM_OBJ face/toe forward Y in Blender
um_vs = np.array([[v.co.x, v.co.y, v.co.z] for v in um_obj.data.vertices])
print(f"UM_OBJ Blender local verts: X=[{um_vs[:,0].min():.3f},{um_vs[:,0].max():.3f}] Y=[{um_vs[:,1].min():.3f},{um_vs[:,1].max():.3f}] Z=[{um_vs[:,2].min():.3f},{um_vs[:,2].max():.3f}]")
feet = um_vs[um_vs[:, 2] < 1.0]
print(f"UM_OBJ Feet (Z<1.0): Y=[{feet[:,1].min():.3f},{feet[:,1].max():.3f}] (front toes side!)")

# Compare Tarn_Robot_LowPoly toes forward Y
tarn_vs = np.array([[v.co.x, v.co.y, v.co.z] for v in robot.data.vertices])
tfeet = tarn_vs[tarn_vs[:, 2] < 1.0]
print(f"Tarn Feet (Z<1.0): Y=[{tfeet[:,1].min():.3f},{tfeet[:,1].max():.3f}]")

# Check handL__Bone vs LeftHand unity_bindpose_pos!
robo_spec = json.loads(UM_BONES_00.read_text(encoding="utf-8"))
for b in robo_spec["bones"]:
    if b["name"] in ("Hips", "Spine", "Spine1", "Neck", "Head", "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand", "RightShoulder", "RightArm", "RightForeArm", "RightHand", "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase", "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase"):
        up = b["unity_bindpose_pos"]
        print(f"UM bone {b['name']:15s}: unity=({up[0]:7.3f},{up[1]:7.3f},{up[2]:7.3f}) -> if(-ux,-uz,uy)=({-up[0]:7.3f},{-up[2]:7.3f},{up[1]:7.3f})")

# Summarize ALL part__* vertex groups of Tarn_Robot_LowPoly
print("\n=== ALL part__* VGs on Tarn_Robot_LowPoly ===")
vg_verts = {vg.index: [] for vg in robot.vertex_groups if vg.name.startswith("part__") or vg.name.startswith("hand")}
for vi, v in enumerate(robot.data.vertices):
    for g in v.groups:
        if g.group in vg_verts and g.weight > 0.01:
            vg_verts[g.group].append(v.co)

for vg in sorted([g for g in robot.vertex_groups if g.name.startswith("part__")], key=lambda g: g.name):
    pts = vg_verts[vg.index]
    if not pts:
        print(f"  {vg.name:28s}: EMPTY")
        continue
    arr = np.array([[p.x, p.y, p.z] for p in pts])
    c = arr.mean(axis=0)
    mn, mx = arr.min(axis=0), arr.max(axis=0)
    print(f"  {vg.name:28s}: n={len(pts):5d} center=({c[0]:6.2f},{c[1]:6.2f},{c[2]:6.2f}) X=[{mn[0]:5.2f},{mx[0]:5.2f}] Y=[{mn[1]:5.2f},{mx[1]:5.2f}] Z=[{mn[2]:5.2f},{mx[2]:5.2f}]")
