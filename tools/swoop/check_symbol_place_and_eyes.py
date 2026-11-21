import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
import bpy
from mathutils import Matrix, Vector

ROOT = Path(r"E:\Agent\TFTF-blender")
TEX_PATH = ROOT / "3rd-party-models/swoop/01_master/textures/Tx_Swoop_D_RGB.png"
img = bpy.data.images.load(str(TEX_PATH))
tw, th = img.size[0], img.size[1]
tex = (np.array(img.pixels[:], dtype=np.float32).reshape((th, tw, 4))[:, :, :3] * 255.0).astype(np.uint8)[::-1].copy()

def uv_px(u, v):
    return ((u - 0.004) / (0.746 - 0.004)) * tw, (1.0 - (v - 0.254) / (0.996 - 0.254)) * th

# 1. Compute exact Posed -> Static transform of bird_Head in Swoop_pbr.fbx
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"))
sw = bpy.data.objects.get("Swoop.001")
sym = bpy.data.objects.get("Symbol_AB")
arm = bpy.data.objects.get("Bip001")

deps = bpy.context.evaluated_depsgraph_get()
sym_posed_ev = sym.evaluated_get(deps).data
sw_posed_ev = sw.evaluated_get(deps).data
# Where was posed Symbol_AB in world vs posed bird_chest/bird_Head?
sym_posed_pts = [sym.matrix_world @ v.co for v in sym_posed_ev.vertices]
bh_posed_world = arm.matrix_world @ arm.pose.bones["bird_Head"].matrix.copy()
bc_posed_world = arm.matrix_world @ arm.pose.bones["bird_chest"].matrix.copy()
sp1_posed_world = arm.matrix_world @ arm.pose.bones["Bip001 Spine1"].matrix.copy()

# Clear pose
arm.animation_data_clear()
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.transforms_clear()
bpy.ops.object.mode_set(mode='OBJECT')
deps = bpy.context.evaluated_depsgraph_get()

bh_unposed_world = arm.matrix_world @ arm.pose.bones["bird_Head"].matrix.copy()
sp1_unposed_world = arm.matrix_world @ arm.pose.bones["Bip001 Spine1"].matrix.copy()

# Evaluate baked Swoop scale transform (same as build_aligned_swoop_robot.py)
sw_st = sw.evaluated_get(deps).data
vs = [v.co for v in sw_st.vertices]
min_x, max_x = min(v.x for v in vs), max(v.x for v in vs)
min_y, max_y = min(v.y for v in vs), max(v.y for v in vs)
min_z, max_z = min(v.z for v in vs), max(v.z for v in vs)
scale_factor = 3.50
center_x = (min_x + max_x) / 2
pelvis_vg = sw.vertex_groups.get("Bone_Pelvis")
pelvis_ys = [v.co.y for v in sw_st.vertices if pelvis_vg and any(g.group == pelvis_vg.index and g.weight > 0.5 for g in v.groups)]
center_y = (sum(pelvis_ys) / len(pelvis_ys)) if pelvis_ys else (min_y + max_y) / 2
mat_xform = Matrix.Translation(Vector((-center_x * scale_factor, -center_y * scale_factor, -min_z * scale_factor))) @ Matrix.Scale(scale_factor, 4)

# Also look at bird_Head in swoop_pbr.fbx BEFORE build_aligned_swoop_robot vs posed!
# Wait: in build_aligned_swoop_robot.py, lines 67-130 pose arms/hands, NOT bird_Head!
# Check where bird_chest/bird_Head gold beak actually is in sw_st (after mat_xform):
pts_local_in_baked = [mat_xform @ v.co for v in sw_st.vertices]
bh_vg = sw.vertex_groups["bird_Head"]
bh_pts_baked = [mat_xform @ v.co for v in sw_st.vertices if any(g.group == bh_vg.index and g.weight > 0.3 for g in v.groups)]
print(f"Unposed bird_Head in baked_swoop: X=[{min(p.x for p in bh_pts_baked):.2f},{max(p.x for p in bh_pts_baked):.2f}] Y=[{min(p.y for p in bh_pts_baked):.2f},{max(p.y for p in bh_pts_baked):.2f}] Z=[{min(p.z for p in bh_pts_baked):.2f},{max(p.z for p in bh_pts_baked):.2f}]")

# Check where gold chest beak vertices in swoop_prepared are!
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/03_fbx/swoop_prepared.fbx"))
rob = bpy.data.objects.get("cha_swoop_robot")
rme = rob.data
ruvl = rme.uv_layers["UV0"].data
vg_names = {vg.index: vg.name for vg in rob.vertex_groups}

# Check Box 1 & Box 2 overlap on Robot and Vehicle
for label, obj_name, fbx_p in (
    ("Robot", "cha_swoop_robot", ROOT / "3rd-party-models/swoop/03_fbx/swoop_prepared.fbx"),
    ("Vehicle", "cha_swoop_vh", ROOT / "3rd-party-models/swoop/03_fbx/swoop_vh_prepared.fbx"),
):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(fbx_p))
    obj = bpy.data.objects.get(obj_name)
    me = obj.data
    uvl = me.uv_layers["UV0"].data
    vgn = {vg.index: vg.name for vg in obj.vertex_groups}
    b1, b2 = {}, {}
    for p in me.polygons:
        pts = [uv_px(uvl[li].uv.x, uvl[li].uv.y) for li in p.loop_indices]
        cx = sum(pt[0] for pt in pts)/len(pts); cy = sum(pt[1] for pt in pts)/len(pts)
        v0 = me.vertices[p.vertices[0]]
        bn = vgn[max(v0.groups, key=lambda g: g.weight).group] if v0.groups else "None"
        rgb = tex[int(np.clip(cy,0,1023)), int(np.clip(cx,0,1023))]
        if 885 <= cx <= 968 and 647 <= cy <= 675:
            b1.setdefault((bn, int(rgb.max() < 75)), []).append((cx, cy, p.center.x, p.center.y, p.center.z))
        if 600 <= cx <= 666 and 5 <= cy <= 34:
            b2.setdefault((bn, int(rgb.max() < 75)), []).append((cx, cy, p.center.x, p.center.y, p.center.z))
    print(f"\n=== {label} Box1 (Robot Visor [885..968, 647..675]) ===")
    for k, items in sorted(b1.items()):
        print(f"  {k}: n={len(items)} Z=[{min(i[4] for i in items):.2f},{max(i[4] for i in items):.2f}] px=[{min(i[0] for i in items):.1f},{max(i[0] for i in items):.1f}] py=[{min(i[1] for i in items):.1f},{max(i[1] for i in items):.1f}]")
    print(f"=== {label} Box2 (Bird Eyes [600..666, 5..34]) ===")
    for k, items in sorted(b2.items()):
        print(f"  {k}: n={len(items)} Z=[{min(i[4] for i in items):.2f},{max(i[4] for i in items):.2f}] px=[{min(i[0] for i in items):.1f},{max(i[0] for i in items):.1f}] py=[{min(i[1] for i in items):.1f},{max(i[1] for i in items):.1f}]")
