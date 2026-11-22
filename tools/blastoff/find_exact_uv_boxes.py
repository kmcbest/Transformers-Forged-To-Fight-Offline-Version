import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

head_obj = bpy.data.objects["RB_Blastoff_CHARSKEL_Head.001.dmx"]
arml_obj = bpy.data.objects["RB_Blastoff_CHARSKEL_ArmLoL.001.dmx"]

# Print all ArmUp UV bounds by fwd/up
def inspect_obj_uvs(obj, filter_fn, label, tex_size):
    uv_layer = obj.data.uv_layers.active
    mat_slots = [s.material.name if s.material else "" for s in obj.material_slots]
    mw = obj.matrix_world
    by_mat = {}
    for poly in obj.data.polygons:
        cw = mw @ poly.center
        fwd, left, up = cw.x, cw.y + 10.0118, cw.z
        if not filter_fn(fwd, left, up, poly):
            continue
        mname = mat_slots[poly.material_index] if poly.material_index < len(mat_slots) else ""
        w, h = tex_size.get(mname, (512, 512))
        for li in poly.loop_indices:
            uv = uv_layer.data[li].uv
            u = uv.x % 1.0
            v = uv.y % 1.0
            px = int(u * w)
            py = int((1.0 - v) * h)
            by_mat.setdefault(mname, []).append((px, py, fwd, left, up))
    print(f"\n=== {label} ===")
    for mname, pts in by_mat.items():
        pxs = [p[0] for p in pts]
        pys = [p[1] for p in pts]
        print(f"  Mat={mname}: {len(pts)} loops, UV_X=[{min(pxs)}..{max(pxs)}], UV_Y=[{min(pys)}..{max(pys)}]")

TS = {
    "RB_Blastoff_Chest_Cust_MatINST": (1024, 1024),
    "RB_Blastoff_Legs_Cust_MatINST": (1024, 1024),
    "RB_Blastoff_Head_Cust_MatINST": (512, 512),
    "RB_Blastoff_ArmLo_Cust_MatINST": (512, 512),
    "RB_Blastoff_ArmUp_Cust_MatINST": (512, 512),
}

# 1. Shoulder front gear arc (ArmUp material, front side fwd > 0, up > 4.2)
inspect_obj_uvs(head_obj, lambda f, l, u, p: u > 4.15 and f > 0.0, "Shoulder Front / Collar (up>4.15, fwd>0)", TS)
# 2. Chest Grille (fwd > 0.35, 3.85 < up < 4.45)
inspect_obj_uvs(head_obj, lambda f, l, u, p: 3.85 < u < 4.45 and f > 0.35, "Chest Grille (3.85<up<4.45, fwd>0.35)", TS)
# 3. Lower Chest / Ribs (fwd > 0.25, 3.35 < up < 3.88)
inspect_obj_uvs(head_obj, lambda f, l, u, p: 3.35 < u < 3.88 and f > 0.25, "Lower Chest Vents (3.35<up<3.88, fwd>0.25)", TS)
# 4. Pelvis (3.0 < up < 3.4)
inspect_obj_uvs(head_obj, lambda f, l, u, p: 2.9 < u < 3.40, "Pelvis (2.9<up<3.4)", TS)
# 5. Front Shin / Lower Legs (0.5 < up < 2.2, fwd > 0.15)
inspect_obj_uvs(head_obj, lambda f, l, u, p: 0.5 < u < 2.2 and f > 0.15, "Front Shin (0.5<up<2.2, fwd>0.15)", TS)
# 6. Forearm Front / Outer (arml_obj)
inspect_obj_uvs(arml_obj, lambda f, l, u, p: True, "Forearm All", TS)
