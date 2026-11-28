import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy, json, math
from mathutils import Vector, Matrix
from pathlib import Path

print("=== [Breakdown] Stage 2B Vehicle Alignment (vehicle_idle01 Frame 1 -> Sideswipe 34-Bone Car Rig) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
BD_DIR = ROOT / "3rd-party-models" / "Breakdown"
FBX_SRC = BD_DIR / "source" / "source" / "Breakdown.fbx"
OUT_FBX_DIR = BD_DIR / "03_fbx_exports"
OUT_FBX_DIR.mkdir(parents=True, exist_ok=True)
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Breakdown"
UNITY_DIR.mkdir(parents=True, exist_ok=True)

SIDESWIPE_VEH_TRUTH = json.loads((BD_DIR / "sideswipe_01_bones.json").read_text(encoding="utf-8"))
SIDESWIPE_34_BONES = [b["name"] for b in SIDESWIPE_VEH_TRUTH["bones"]]
ss_veh_pos = {
    b["name"]: Vector((-float(b["unity_pos"][0]), -float(b["unity_pos"][2]), float(b["unity_pos"][1])))
    for b in SIDESWIPE_VEH_TRUTH["bones"]
}


def bake_evaluated_copy(src_obj, new_name: str):
    deps = bpy.context.evaluated_depsgraph_get()
    baked_data = bpy.data.meshes.new_from_object(src_obj.evaluated_get(deps))
    baked_data.name = new_name + "_mesh"
    baked_data.transform(src_obj.matrix_world)
    baked_data.update()
    new_obj = bpy.data.objects.new(new_name, baked_data)
    bpy.context.scene.collection.objects.link(new_obj)
    return new_obj


def wrap_polygon_uvs_clean(mesh_obj):
    uvd = mesh_obj.data.uv_layers.active.data
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
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

    src_car = bpy.data.objects.get("Breakdown.001")
    src_sym = bpy.data.objects.get("Symbol_DC02")
    assert src_car and src_sym, "Missing Breakdown.001 or Symbol_DC02!"

    sym_mat_indices = [p.material_index for p in src_sym.data.polygons]
    veh_obj = bake_evaluated_copy(src_car, "cha_breakdown_veh")
    sym_obj = bake_evaluated_copy(src_sym, "cha_breakdown_veh_sym")

    keep = {veh_obj, sym_obj}
    for o in list(bpy.data.objects):
        if o not in keep:
            bpy.data.objects.remove(o, do_unlink=True)

    # Smooth normals & wrap mirrored UVs
    veh_obj.data.polygons.foreach_set("use_smooth", [True] * len(veh_obj.data.polygons))
    veh_obj.data.update()
    shifted = wrap_polygon_uvs_clean(veh_obj)
    print(f"[*] Wrapped {shifted} mirrored-UV polygons on Breakdown Countach cleanly into [0, 1]")

    # Scale uniformly to Sideswipe car length (9.193m: Unity Z=[-4.557, +4.636])
    ys = [v.co.y for v in veh_obj.data.vertices]
    raw_len = max(ys) - min(ys)
    TARGET_LEN = 9.193
    SCALE_VEH = TARGET_LEN / raw_len
    print(f"[*] Car raw length={raw_len:.5f} -> uniform scale={SCALE_VEH:.4f} (Target Sideswipe length={TARGET_LEN:.3f}m)")
    s_mat = Matrix.Scale(SCALE_VEH, 4)
    veh_obj.data.transform(s_mat)
    sym_obj.data.transform(s_mat)

    # Verify nose (Symbol_DC02 & low wedge) faces -Y in Blender (= +Z forward in Unity!)
    sym_cy = sum(v.co.y for v in sym_obj.data.vertices) / len(sym_obj.data.vertices)
    print(f"[*] Symbol_DC02 hood crest centerY={sym_cy:+.3f} (must be < 0 so Countach nose faces +Z Unity forward)")
    if sym_cy > 0.0:
        rot_180 = Matrix.Rotation(math.pi, 4, 'Z')
        veh_obj.data.transform(rot_180)
        sym_obj.data.transform(rot_180)
        print("[*] Rotated 180 deg around Z to align nose forward.")

    # Align center to X=0, Blender Y=-0.040 (Unity Z=[-4.557,+4.636] center=+0.040), ground min Z=+0.030 (matching Sideswipe Y_min=0.030)
    vs = [v.co for v in veh_obj.data.vertices]
    cx = (min(v.x for v in vs) + max(v.x for v in vs)) / 2.0
    cy = (min(v.y for v in vs) + max(v.y for v in vs)) / 2.0
    min_z = min(v.z for v in vs)
    align_mat = Matrix.Translation(Vector((-cx, -cy - 0.040, -min_z + 0.030)))
    veh_obj.data.transform(align_mat)
    sym_obj.data.transform(align_mat)

    # Lift hood Symbol_DC02 +0.015m upward (+Z) & stamp SubMesh 1 purple/charcoal UVs
    sym_obj.data.transform(Matrix.Translation(Vector((0.0, 0.0, 0.015))))
    target_uv = veh_obj.data.uv_layers[0].name if veh_obj.data.uv_layers else "UV0"
    if not sym_obj.data.uv_layers:
        sym_obj.data.uv_layers.new(name=target_uv)
    else:
        sym_obj.data.uv_layers.active.name = target_uv
    uvl = sym_obj.data.uv_layers[target_uv].data
    for idx_p, p in enumerate(sym_obj.data.polygons):
        mi = sym_mat_indices[idx_p] if idx_p < len(sym_mat_indices) else 0
        t_uv = (0.25, 0.50) if mi == 0 else (0.75, 0.50)
        for li in p.loop_indices:
            uvl[li].uv = t_uv

    mat_main = bpy.data.materials.new(name="cha_breakdown_main")
    mat_sym = bpy.data.materials.new(name="cha_breakdown_sym")
    veh_obj.data.materials.clear()
    veh_obj.data.materials.append(mat_main)
    sym_obj.data.materials.clear()
    sym_obj.data.materials.append(mat_sym)

    fin_vs = [v.co for v in veh_obj.data.vertices]
    print(f"[✓] Aligned Countach bounds: X=[{min(v.x for v in fin_vs):.3f},{max(v.x for v in fin_vs):.3f}], Y=[{min(v.y for v in fin_vs):.3f},{max(v.y for v in fin_vs):.3f}], Z=[{min(v.z for v in fin_vs):.3f},{max(v.z for v in fin_vs):.3f}]")

    bpy.ops.object.select_all(action='DESELECT')
    sym_obj.select_set(True)
    veh_obj.select_set(True)
    bpy.context.view_layer.objects.active = veh_obj
    bpy.ops.object.join()

    # Bind 100% rigidly to 'chop2_hip_center' (parent=BodyBase on Sideswipe_01 34-bone hierarchy)
    veh_obj.vertex_groups.clear()
    vgs = {bn: veh_obj.vertex_groups.new(name=bn) for bn in SIDESWIPE_34_BONES}
    vgs["chop2_hip_center"].add(list(range(len(veh_obj.data.vertices))), 1.0, 'REPLACE')
    print(f"[✓] Countach bound 100% to chop2_hip_center ({len(veh_obj.data.vertices)} verts, materials={len(veh_obj.data.materials)})")

    arm_data = bpy.data.armatures.new("cha_sideswipe_GS_Deluxe2008_01_arm")
    arm_obj = bpy.data.objects.new("cha_sideswipe_GS_Deluxe2008_01_arm", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    for bn in SIDESWIPE_34_BONES:
        b = arm_data.edit_bones.new(bn)
        p = ss_veh_pos[bn]
        b.head = p
        b.tail = p + Vector((0.0, 0.0, 0.3))
    bpy.ops.object.mode_set(mode='OBJECT')

    veh_obj.parent = arm_obj
    mod = veh_obj.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm_obj

    blend_dir = BD_DIR / "01_aligned_mesh"
    blend_dir.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_dir / "breakdown_veh_aligned.blend"))

    for out_fbx in (OUT_FBX_DIR / "breakdown_veh_prepared.fbx", UNITY_DIR / "breakdown_veh_prepared.fbx"):
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
