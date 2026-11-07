import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import math
from pathlib import Path
import bpy
import mathutils

ROOT = Path(r"E:\Agent\TFTF-blender")
BONES_JSON = ROOT / "tools" / "demolishor" / "ironhide_80_bones.json"
MASTER_BLEND = ROOT / "3rd-party-models" / "onslaught" / "onslaught_master.blend"

bpy.ops.wm.open_mainfile(filepath=str(MASTER_BLEND))

ons_arm = bpy.data.objects["Onslaught_ARM"]
scale_factor = 1.725
ons_arm.scale = (scale_factor, scale_factor, scale_factor)
ons_arm.rotation_euler = (0.0, 0.0, math.radians(90.0))
bpy.context.view_layer.update()

print("=== 1. WHEEL & CAP & LEGS INSPECTION (AFTER SCALE + Z90) ===")
depsgraph = bpy.context.evaluated_depsgraph_get()
check_names = [
    "RB_Onslaught_CHARSKEL_CapL.mo.dmx",
    "RB_Onslaught_CHARSKEL_CapR.mo.dmx",
    "RB_Onslaught_CHARSKEL_Chest.mo.dmx",
    "RB_Onslaught_CHARSKEL_Legs.mo.dmx",
    "RB_Onslaught_CHARSKEL_ArmLoL.mo.dmx",
    "RB_Onslaught_CHARSKEL_ArmLoR.mo.dmx",
    "RB_Onslaught_STAT_Wheel.mo.005.dmx",
    "RB_Onslaught_STAT_Wheel.mo.006.dmx",
    "RB_Onslaught_STAT_Wheel.mo.007.dmx",
    "RB_Onslaught_STAT_Wheel.mo.008.dmx",
]

for nm in check_names:
    obj = bpy.data.objects.get(nm)
    if not obj:
        print(f"MISSING: {nm}")
        continue
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    verts_w = [eval_obj.matrix_world @ v.co for v in mesh.vertices]
    cx = sum(v.x for v in verts_w) / len(verts_w)
    cy = sum(v.y for v in verts_w) / len(verts_w)
    cz = sum(v.z for v in verts_w) / len(verts_w)
    eval_obj.to_mesh_clear()

    vg_counts = {}
    for v in obj.data.vertices:
        for g in v.groups:
            if g.weight > 0.01:
                vgn = obj.vertex_groups[g.group].name
                vg_counts[vgn] = vg_counts.get(vgn, 0) + 1
    print(f"\n[{nm}] parent={obj.parent.name if obj.parent else None} parent_bone='{obj.parent_bone}'")
    print(f"  World Center: ({cx:6.3f}, {cy:6.3f}, {cz:6.3f})")
    print(f"  VGs: {vg_counts}")

print("\n=== 2. ONS_ARM FINGER / HAND BONES ===")
for b in ons_arm.data.bones:
    if any(k in b.name.lower() for k in ["hand", "thumb", "index", "middle", "ring", "pinky", "finger", "arm", "shoulder", "pad", "clav", "wheel"]):
        wpos = (ons_arm.matrix_world @ ons_arm.pose.bones[b.name].matrix).translation
        print(f"  FOC Bone {b.name:28s} parent={b.parent.name if b.parent else None:24s} pos=({wpos.x:6.3f}, {wpos.y:6.3f}, {wpos.z:6.3f})")

print("\n=== 3. IRONHIDE 80 BONES (ARM / HAND / FINGER / LEG) ===")
with open(BONES_JSON, "r", encoding="utf-8") as f:
    bdata = json.load(f)
for bname in bdata["bone_order"]:
    if any(k in bname.lower() for k in ["hand", "thumb", "index", "middle", "ring", "pinky", "finger", "arm", "shoulder", "leg", "foot"]):
        mat = mathutils.Matrix(bdata["bones"][bname]["matrix"])
        t = mat.to_translation()
        # Unity (x, y, z) -> Blender (x, z, y)
        print(f"  IH Bone  {bname:28s} parent={str(bdata['bones'][bname].get('parent')):20s} blender_pos=({t.x:6.3f}, {t.z:6.3f}, {t.y:6.3f})")
