import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy, json
from mathutils import Vector, Matrix
from pathlib import Path

print("=== [WildRider] Stage 2B Vehicle Alignment (Unity-Native Baked vehicle_idle01 -> Prowl 26-Bone Car Rig) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
WR_DIR = ROOT / "3rd-party-models" / "WildRider"
FBX_SRC = WR_DIR / "source" / "WildRider_pbr.fbx"
OUT_FBX_DIR = WR_DIR / "03_fbx_exports"
OUT_FBX_DIR.mkdir(parents=True, exist_ok=True)
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "WildRider"
UNITY_DIR.mkdir(parents=True, exist_ok=True)

BAKED_CAR_OBJ = OUT_FBX_DIR / "wildrider_veh_unity_baked.obj"
BAKED_SYM_OBJ = OUT_FBX_DIR / "wildrider_veh_sym_unity_baked.obj"
BAKED_WEIGHTS = OUT_FBX_DIR / "wildrider_veh_unity_weights.json"

PROWL_VEH_TRUTH = json.loads((WR_DIR / "prowl_26_vehicle_bones.json").read_text(encoding="utf-8"))
PROWL_26_BONES = [b["name"] for b in PROWL_VEH_TRUTH["bones"]]
prowl_veh_pos = {
    b["name"]: Vector((-float(b["unity_pos"][0]), -float(b["unity_pos"][2]), float(b["unity_pos"][1])))
    for b in PROWL_VEH_TRUTH["bones"]
}


def load_unity_baked_obj(obj_path: Path, name: str):
    """Parse OBJ exported from Unity (X-left, Y-up, Z-fwd) -> Blender (-X, -Z, Y) preserving UVs & winding."""
    verts, vns, vts, faces = [], [], [], []
    for line in obj_path.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("v "):
            _, x, y, z = line.split()[:4]
            verts.append(Vector((-float(x), -float(z), float(y))))
        elif line.startswith("vn "):
            _, x, y, z = line.split()[:4]
            vns.append(Vector((-float(x), -float(z), float(y))).normalized())
        elif line.startswith("vt "):
            _, u, v = line.split()[:3]
            vts.append((float(u), float(v)))
        elif line.startswith("f "):
            parts = line.split()[1:4]
            tri = [int(p.split("/")[0]) - 1 for p in parts]
            # Converting Left-Handed Unity (-ux, -uz, uy) -> Right-Handed Blender flips det(-1): invert winding!
            tri = [tri[0], tri[2], tri[1]]
            faces.append(tri)

    # Double-check average face normal against exported vn; flip globally if inverted
    if vns and faces:
        dot_sum = 0.0
        for a, b, c in faces[:2000]:
            fn = (verts[b] - verts[a]).cross(verts[c] - verts[a])
            if fn.length_squared > 1e-16:
                dot_sum += fn.normalized().dot(vns[a])
        if dot_sum < 0.0:
            faces = [[a, c, b] for a, b, c in faces]

    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.uv_layers.new(name="UV0")
    uv_data = me.uv_layers["UV0"].data
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            if vi < len(vts):
                uv_data[li].uv = vts[vi]
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def main():
    assert BAKED_CAR_OBJ.exists() and BAKED_SYM_OBJ.exists() and BAKED_WEIGHTS.exists(), "Run Unity native car baker first!"

    # Grab exact Symbol_DC001 polygon material_index (0=purple crest, 1=charcoal backing) from source FBX
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))
    sym_src = bpy.data.objects.get("Symbol_DC001")
    sym_mat_indices = [p.material_index for p in sym_src.data.polygons] if sym_src else []

    bpy.ops.wm.read_factory_settings(use_empty=True)
    veh_obj = load_unity_baked_obj(BAKED_CAR_OBJ, "cha_wildrider_veh")
    sym_obj = load_unity_baked_obj(BAKED_SYM_OBJ, "cha_wildrider_veh_sym")

    tire_weights = json.loads(BAKED_WEIGHTS.read_text(encoding="utf-8-sig"))
    tire_vert_set = set()
    for idxs in tire_weights.values():
        tire_vert_set.update(idxs)

    # Scale uniformly to match Prowl car length (8.461m) while keeping seamless Unity pose & circular wheels!
    ys = [v.co.y for v in veh_obj.data.vertices]
    raw_len = max(ys) - min(ys)
    TARGET_LEN = 8.461
    SCALE_VEH = TARGET_LEN / raw_len
    print(f"[*] Unity-baked vehicle raw length={raw_len:.5f} -> uniform scale={SCALE_VEH:.4f} (Target Prowl length={TARGET_LEN:.3f}m)")

    s_mat = Matrix.Scale(SCALE_VEH, 4)
    veh_obj.data.transform(s_mat)
    sym_obj.data.transform(s_mat)

    # Align bounds to Prowl 01: X centered at 0, Y centered at -0.1855 (Z_unity = [-4.045, +4.416]), min Z = 0.016
    vs = [v.co for v in veh_obj.data.vertices]
    cx = (min(v.x for v in vs) + max(v.x for v in vs)) / 2.0
    cy = (min(v.y for v in vs) + max(v.y for v in vs)) / 2.0
    min_z = min(v.z for v in vs)
    align_mat = Matrix.Translation(Vector((-cx, -cy - 0.1855, -min_z + 0.016)))
    veh_obj.data.transform(align_mat)
    sym_obj.data.transform(align_mat)

    # Lift hood emblem +0.015m upward (+Z) & assign Decepticon Purple/Charcoal safe UVs
    sym_obj.data.transform(Matrix.Translation(Vector((0.0, 0.0, 0.015))))
    uvl = sym_obj.data.uv_layers["UV0"].data
    for idx_p, p in enumerate(sym_obj.data.polygons):
        mi = sym_mat_indices[idx_p] if idx_p < len(sym_mat_indices) else 0
        t_uv = (0.296875, 0.9375) if mi == 0 else (0.34375, 0.9375)
        for li in p.loop_indices:
            uvl[li].uv = t_uv

    mat_main = bpy.data.materials.new(name="cha_wildrider_main")
    veh_obj.data.materials.clear()
    veh_obj.data.materials.append(mat_main)
    sym_obj.data.materials.clear()
    sym_obj.data.materials.append(mat_main)

    fin_vs = [v.co for v in veh_obj.data.vertices]
    print(f"[✓] Aligned Unity-baked vehicle bounds: X=[{min(v.x for v in fin_vs):.3f},{max(v.x for v in fin_vs):.3f}], Y=[{min(v.y for v in fin_vs):.3f},{max(v.y for v in fin_vs):.3f}], Z=[{min(v.z for v in fin_vs):.3f},{max(v.z for v in fin_vs):.3f}]")

    # Classify tires by physical quadrant in aligned vehicle space (+X Left, -X Right; -Y Front, +Y Rear)
    wheel_bone_assign = {}
    wheel_pts = {"WheeFrontlLeft_R": [], "WheelFrontRight_R": [], "WheelRearLeft_R": [], "WheelRearRight_R": []}
    for v in veh_obj.data.vertices:
        if v.index in tire_vert_set:
            is_left = v.co.x > 0
            is_front = v.co.y < 0
            if is_left and is_front:
                wb = "WheeFrontlLeft_R"
            elif (not is_left) and is_front:
                wb = "WheelFrontRight_R"
            elif is_left and (not is_front):
                wb = "WheelRearLeft_R"
            else:
                wb = "WheelRearRight_R"
            wheel_bone_assign[v.index] = wb
            wheel_pts[wb].append(v.co)

    print("[*] Tire centers vs Prowl Wheel*_R BindPose centers:")
    for wb, pts in wheel_pts.items():
        if pts:
            avg = sum(pts, Vector()) / len(pts)
            p_tgt = prowl_veh_pos[wb]
            print(f"  {wb:20s} ({len(pts):3d}v): WildRider=({avg.x:6.3f}, {avg.y:6.3f}, {avg.z:6.3f}) vs Prowl=({p_tgt.x:6.3f}, {p_tgt.y:6.3f}, {p_tgt.z:6.3f})")

    # Join hood emblem into vehicle mesh
    bpy.ops.object.select_all(action='DESELECT')
    sym_obj.select_set(True)
    veh_obj.select_set(True)
    bpy.context.view_layer.objects.active = veh_obj
    bpy.ops.object.join()

    veh_obj.vertex_groups.clear()
    vgs = {bn: veh_obj.vertex_groups.new(name=bn) for bn in PROWL_26_BONES}
    body_verts = []
    wheel_vlists = {wb: [] for wb in wheel_pts}
    for i in range(len(veh_obj.data.vertices)):
        if i in wheel_bone_assign:
            wheel_vlists[wheel_bone_assign[i]].append(i)
        else:
            body_verts.append(i)

    vgs["COG"].add(body_verts, 1.0, 'REPLACE')
    for wb, idxs in wheel_vlists.items():
        if idxs:
            vgs[wb].add(idxs, 1.0, 'REPLACE')
    print(f"[✓] Vehicle weights: COG={len(body_verts)} verts, Wheels={ {k: len(v) for k, v in wheel_vlists.items()} }")

    # Build Prowl 26-Bone Vehicle Armature
    arm_data = bpy.data.armatures.new("cha_prowl_gs_deluxe2016_01_arm")
    arm_obj = bpy.data.objects.new("cha_prowl_gs_deluxe2016_01_arm", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')

    cog_b = arm_data.edit_bones.new("COG")
    cog_b.head = prowl_veh_pos["COG"]
    cog_b.tail = cog_b.head + Vector((0.0, 0.0, 0.5))

    for bn in PROWL_26_BONES:
        if bn == "COG":
            continue
        b = arm_data.edit_bones.new(bn)
        p = prowl_veh_pos[bn]
        b.head = p
        b.tail = p + Vector((0.0, 0.0, 0.3))
        b.parent = cog_b

    bpy.ops.object.mode_set(mode='OBJECT')
    veh_obj.parent = arm_obj
    mod = veh_obj.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm_obj

    blend_dir = WR_DIR / "01_aligned_mesh"
    blend_dir.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_dir / "wildrider_veh_aligned.blend"))

    for out_fbx in (OUT_FBX_DIR / "wildrider_veh_prepared.fbx", UNITY_DIR / "wildrider_veh_prepared.fbx"):
        bpy.ops.object.select_all(action='DESELECT')
        arm_obj.select_set(True)
        veh_obj.select_set(True)
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.export_scene.fbx(
            filepath=str(out_fbx),
            use_selection=True,
            use_active_collection=False,
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_ALL',
            bake_space_transform=False,
            object_types={'ARMATURE', 'MESH'},
            use_mesh_modifiers=True,
            mesh_smooth_type='FACE',
            add_leaf_bones=False,
            primary_bone_axis='Y',
            secondary_bone_axis='X',
            axis_forward='-Z',
            axis_up='Y',
            armature_nodetype='NULL',
            bake_anim=False,
        )
        print(f"[✓] Exported {out_fbx} ({out_fbx.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
