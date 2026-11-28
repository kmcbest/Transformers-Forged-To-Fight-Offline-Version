import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy, json, math
from mathutils import Vector, Matrix
from pathlib import Path

print("=== [DragStrip] Stage 2B F1 Vehicle Alignment (Unity-Native Baked vehicle_idle01 -> Mirage 30-Bone F1 Rig) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
DS_DIR = ROOT / "3rd-party-models" / "DragStrip"
FBX_SRC = DS_DIR / "source" / "source" / "Dragstrip.fbx"
OUT_FBX_DIR = DS_DIR / "03_fbx_exports"
OUT_FBX_DIR.mkdir(parents=True, exist_ok=True)
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "DragStrip"
UNITY_DIR.mkdir(parents=True, exist_ok=True)

BAKED_CAR_OBJ = OUT_FBX_DIR / "dragstrip_veh_unity_baked.obj"
BAKED_SYM_OBJ = OUT_FBX_DIR / "dragstrip_veh_sym_unity_baked.obj"

MIRAGE_VEH_TRUTH = json.loads((DS_DIR / "mirage_01_bones.json").read_text(encoding="utf-8"))
MIRAGE_30_BONES = [b["name"] for b in MIRAGE_VEH_TRUTH["bones"]]
mirage_veh_pos = {
    b["name"]: Vector((-float(b["unity_pos"][0]), -float(b["unity_pos"][2]), float(b["unity_pos"][1])))
    for b in MIRAGE_VEH_TRUTH["bones"]
}


def load_unity_baked_obj(obj_path: Path, name: str):
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
            faces.append([tri[0], tri[2], tri[1]])

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


def wrap_polygon_uvs_clean(mesh_obj):
    uvd = mesh_obj.data.uv_layers["UV0"].data
    shifted = 0
    for p in mesh_obj.data.polygons:
        us = [uvd[li].uv.x for li in p.loop_indices]
        if min(us) >= 0.99:
            for li in p.loop_indices:
                uvd[li].uv.x -= 1.0
            shifted += 1
        for li in p.loop_indices:
            uvd[li].uv.x = min(0.9995, max(0.0005, uvd[li].uv.x))
            uvd[li].uv.y = min(0.9995, max(0.0005, uvd[li].uv.y))
    return shifted


def main():
    assert BAKED_CAR_OBJ.exists() and BAKED_SYM_OBJ.exists(), "Run Unity native F1 baker first!"

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))
    sym_src = bpy.data.objects.get("Symbol_DC")
    sym_mat_indices = [p.material_index for p in sym_src.data.polygons] if sym_src else []

    bpy.ops.wm.read_factory_settings(use_empty=True)
    veh_obj = load_unity_baked_obj(BAKED_CAR_OBJ, "cha_dragstrip_veh")
    sym_obj = load_unity_baked_obj(BAKED_SYM_OBJ, "cha_dragstrip_veh_sym")

    shifted = wrap_polygon_uvs_clean(veh_obj)
    print(f"[*] Wrapped {shifted} mirrored-UV polygons on F1 vehicle cleanly into [0, 1]")

    # Scale uniformly to Mirage F1 length (9.200m: Unity Z=[-4.615, +4.585])
    ys = [v.co.y for v in veh_obj.data.vertices]
    raw_len = max(ys) - min(ys)
    TARGET_LEN = 9.200
    SCALE_VEH = TARGET_LEN / raw_len
    print(f"[*] F1 raw length={raw_len:.5f} -> uniform scale={SCALE_VEH:.4f} (Target Mirage length={TARGET_LEN:.3f}m)")
    s_mat = Matrix.Scale(SCALE_VEH, 4)
    veh_obj.data.transform(s_mat)
    sym_obj.data.transform(s_mat)

    # Rotate 180 deg around Z (det=+1 rigid transform) so pointy F1 nose aligns forward (+Z Unity) matching Mirage F1!
    rot_180 = Matrix.Rotation(math.pi, 4, 'Z')
    veh_obj.data.transform(rot_180)
    sym_obj.data.transform(rot_180)

    # Center X=0, Y center=+0.015 (so DetectVehAxisSpec sz=+1f matches Mirage Unity Z=[-4.615,+4.585]), ground min Z=-0.013
    vs = [v.co for v in veh_obj.data.vertices]
    cx = (min(v.x for v in vs) + max(v.x for v in vs)) / 2.0
    cy = (min(v.y for v in vs) + max(v.y for v in vs)) / 2.0
    min_z = min(v.z for v in vs)
    align_mat = Matrix.Translation(Vector((-cx, -cy + 0.015, -min_z - 0.013)))
    veh_obj.data.transform(align_mat)
    sym_obj.data.transform(align_mat)

    # Lift nose Symbol_DC +0.015m upward (+Z) & stamp Decepticon Purple/Charcoal UVs
    sym_obj.data.transform(Matrix.Translation(Vector((0.0, 0.0, 0.015))))
    uvl = sym_obj.data.uv_layers["UV0"].data
    for idx_p, p in enumerate(sym_obj.data.polygons):
        mi = sym_mat_indices[idx_p] if idx_p < len(sym_mat_indices) else 0
        t_uv = (0.867188, 0.914062) if mi == 0 else (0.929688, 0.914062)
        for li in p.loop_indices:
            uvl[li].uv = t_uv

    mat_main = bpy.data.materials.new(name="cha_dragstrip_main")
    veh_obj.data.materials.clear()
    veh_obj.data.materials.append(mat_main)
    sym_obj.data.materials.clear()
    sym_obj.data.materials.append(mat_main)

    fin_vs = [v.co for v in veh_obj.data.vertices]
    print(f"[✓] Aligned F1 bounds: X=[{min(v.x for v in fin_vs):.3f},{max(v.x for v in fin_vs):.3f}], Y=[{min(v.y for v in fin_vs):.3f},{max(v.y for v in fin_vs):.3f}], Z=[{min(v.z for v in fin_vs):.3f},{max(v.z for v in fin_vs):.3f}]")

    bpy.ops.object.select_all(action='DESELECT')
    sym_obj.select_set(True)
    veh_obj.select_set(True)
    bpy.context.view_layer.objects.active = veh_obj
    bpy.ops.object.join()

    # Bind 100% rigidly to 'COG' (Mirage 30 bones are transform-piece chop bones, not wheel spin bones)
    veh_obj.vertex_groups.clear()
    vgs = {bn: veh_obj.vertex_groups.new(name=bn) for bn in MIRAGE_30_BONES}
    vgs["COG"].add(list(range(len(veh_obj.data.vertices))), 1.0, 'REPLACE')
    print(f"[✓] F1 vehicle bound 100% to COG ({len(veh_obj.data.vertices)} verts)")

    arm_data = bpy.data.armatures.new("cha_mirage_gs_deluxe2016_01_arm")
    arm_obj = bpy.data.objects.new("cha_mirage_gs_deluxe2016_01_arm", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')

    cog_b = arm_data.edit_bones.new("COG")
    cog_b.head = mirage_veh_pos["COG"]
    cog_b.tail = cog_b.head + Vector((0.0, 0.0, 0.5))

    for bn in MIRAGE_30_BONES:
        if bn == "COG":
            continue
        b = arm_data.edit_bones.new(bn)
        p = mirage_veh_pos[bn]
        b.head = p
        b.tail = p + Vector((0.0, 0.0, 0.3))
        b.parent = cog_b

    bpy.ops.object.mode_set(mode='OBJECT')
    veh_obj.parent = arm_obj
    mod = veh_obj.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm_obj

    blend_dir = DS_DIR / "01_aligned_mesh"
    blend_dir.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_dir / "dragstrip_veh_aligned.blend"))

    for out_fbx in (OUT_FBX_DIR / "dragstrip_veh_prepared.fbx", UNITY_DIR / "dragstrip_veh_prepared.fbx"):
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
