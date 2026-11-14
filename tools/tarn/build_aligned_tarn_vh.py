import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
from pathlib import Path
import bmesh
import bpy
from mathutils import Vector

print("=== BUILDING RIGGED TARN VEHICLE (CYBERTRONIAN TANK) FOR ULTRA MAGNUS _01 ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
TARN_DIR = ROOT / "3rd-party-models" / "Tarn"
BAKED_BLEND = TARN_DIR / "06_working" / "tarn_workspace_baked.blend"
UM_BONES_01 = TARN_DIR / "04_donor_reference" / "ultramagnus_gs_leader" / "cha_ultramagnus_gs_leader_01_bones.json"
UM_OBJ_01 = TARN_DIR / "04_donor_reference" / "ultramagnus_gs_leader" / "cha_ultramagnus_gs_leader_01_alt.obj"
TEX_DIR = TARN_DIR / "06_working" / "unified_textures"
FBX_EXPORT_DIR = TARN_DIR / "06_working" / "fbx_exports"
UNITY_TARN_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Tarn"
SCRATCH_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\66aaeff3-2652-4f24-8fc9-00b0ef375582\scratch")


def um_unity_to_blender(upos):
    return Vector((-float(upos[0]), -float(upos[2]), float(upos[1])))


def weld_and_decimate(obj, target_faces=None, weld_dist=0.0002):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Apply existing world transform into mesh coords safely
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.modifiers.clear()

    # Weld split islands (preserving UVs)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld_dist)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()

    # Clear corrupt custom split normals, use crisp 38-deg autosmooth
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.data.use_auto_smooth = True
    obj.data.auto_smooth_angle = 0.663  # ~38 deg

    if target_faces and len(obj.data.polygons) > target_faces:
        m = obj.modifiers.new("DecTank", "DECIMATE")
        m.decimate_type = "COLLAPSE"
        m.ratio = target_faces / float(len(obj.data.polygons))
        m.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=m.name)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BAKED_BLEND))
    parts = []
    for nm in ("TarnTank_Mesh", "TarnTankTreadL_Mesh", "TarnTankTreadR_Mesh"):
        o = bpy.data.objects.get(nm)
        assert o is not None, f"Missing {nm}"
        parts.append(o)

    weld_and_decimate(parts[0], target_faces=15500, weld_dist=0.0002)
    weld_and_decimate(parts[1], target_faces=2800, weld_dist=0.0002)
    weld_and_decimate(parts[2], target_faces=2800, weld_dist=0.0002)

    # Join into single unified Tarn_Vehicle_LowPoly
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    tank = bpy.context.active_object
    tank.name = "Tarn_Vehicle_LowPoly"

    # Keep only UVMap (UV0 matching cha_tarn_tform_misc_A.png)
    for idx in range(len(tank.data.uv_layers) - 1, -1, -1):
        uv = tank.data.uv_layers[idx]
        if uv.name != "UVMap":
            try:
                tank.data.uv_layers.remove(uv)
            except Exception:
                pass
    if "UVMap" in tank.data.uv_layers:
        tank.data.uv_layers["UVMap"].active = True
        tank.data.uv_layers["UVMap"].active_render = True

    # Apply unified vehicle texture material
    mat = bpy.data.materials.new("MAT_Tarn_Vehicle")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    ta = nt.nodes.new("ShaderNodeTexImage")
    ta.image = bpy.data.images.load(str(TEX_DIR / "cha_tarn_tform_misc_A.png"))
    nt.links.new(ta.outputs["Color"], bsdf.inputs["Base Color"])
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = bpy.data.images.load(str(TEX_DIR / "cha_tarn_tform_misc_NM_std.png"))
    tn.image.colorspace_settings.name = "Non-Color"
    nm_node = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nm_node.inputs["Color"])
    nt.links.new(nm_node.outputs["Normal"], bsdf.inputs["Normal"])
    te = nt.nodes.new("ShaderNodeTexImage")
    te.image = bpy.data.images.load(str(TEX_DIR / "cha_tarn_tform_misc_Emission.png"))
    nt.links.new(te.outputs["Color"], bsdf.inputs["Emission"])
    bsdf.inputs["Emission Strength"].default_value = 3.0
    bsdf.inputs["Roughness"].default_value = 0.55
    tank.data.materials.clear()
    tank.data.materials.append(mat)

    # Uniform scale (0.90x), center X=0, Y=0, and ground Z_min = 0.000 (matching UM_01 alt-mode floor!)
    VH_SCALE = 0.90
    bpy.ops.object.select_all(action="DESELECT")
    tank.select_set(True)
    bpy.context.view_layer.objects.active = tank
    tank.scale = (VH_SCALE, VH_SCALE, VH_SCALE)
    bpy.ops.object.transform_apply(scale=True)

    xs = [v.co.x for v in tank.data.vertices]
    ys = [v.co.y for v in tank.data.vertices]
    zs = [v.co.z for v in tank.data.vertices]
    cx = 0.5 * (min(xs) + max(xs))
    cy = 0.5 * (min(ys) + max(ys))
    z_min = min(zs)
    for v in tank.data.vertices:
        v.co.x -= cx
        v.co.y -= cy
        v.co.z -= z_min
    tank.data.update()

    xs = [v.co.x for v in tank.data.vertices]
    ys = [v.co.y for v in tank.data.vertices]
    zs = [v.co.z for v in tank.data.vertices]
    print(
        f"[✓] Tarn_Vehicle_LowPoly ready: verts={len(tank.data.vertices)}, polys={len(tank.data.polygons)}, "
        f"X=[{min(xs):.2f},{max(xs):.2f}], Y=[{min(ys):.2f},{max(ys):.2f}], Z=[{min(zs):.3f},{max(zs):.2f}]"
    )

    # Clear all source VGs and bind rigidly to Ultra Magnus _01 audited steady chassis bone (chop1_backpack_main_center preserves scl=1.00 across SP3 & Heavy!)
    tank.vertex_groups.clear()
    alt_spec = json.loads(UM_BONES_01.read_text(encoding="utf-8"))
    for b in alt_spec["bones"]:
        tank.vertex_groups.new(name=b["name"])
    vg_chassis = tank.vertex_groups["chop1_backpack_main_center"]
    vg_chassis.add(list(range(len(tank.data.vertices))), 1.0, "REPLACE")

    # Build export armature ARM_Tarn_UM40 matching exact Ultra Magnus _01 bindpose bones
    arm_data = bpy.data.armatures.new("ARM_Tarn_UM40_Data")
    arm_obj = bpy.data.objects.new("ARM_Tarn_UM40", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = arm_data.edit_bones

    for nm, pos in [("Reference", (0, 0, 0)), ("COG", (0, 0, 0)), ("BodyBase", (0, 0, 0)), ("Trailer", (0, -1.815, 3.35))]:
        eb = ebs.new(nm)
        eb.head = Vector(pos)
        eb.tail = Vector(pos) + Vector((0, -0.4, 0))
    ebs["COG"].parent = ebs["Reference"]
    ebs["BodyBase"].parent = ebs["COG"]
    ebs["Trailer"].parent = ebs["BodyBase"]

    for b in alt_spec["bones"]:
        nm = b["name"]
        p = um_unity_to_blender(b["unity_bindpose_pos"])
        eb = ebs.get(nm) or ebs.new(nm)
        eb.head = p
        eb.tail = p + Vector((0, -0.35, 0))
    for b in alt_spec["bones"]:
        nm = b["name"]
        par = b["parent"]
        ebs[nm].parent = ebs[par] if par in ebs else ebs["BodyBase"]
        ebs[nm].use_connect = False

    bpy.ops.object.mode_set(mode="OBJECT")
    tank.parent = arm_obj
    mod = tank.modifiers.new("Armature", "ARMATURE")
    mod.object = arm_obj

    for o in list(bpy.data.objects):
        o.select_set(o in (arm_obj, tank))

    for out_fbx in (FBX_EXPORT_DIR / "tarn_tank_prepared.fbx", UNITY_TARN_DIR / "tarn_tank_prepared.fbx"):
        bpy.ops.export_scene.fbx(
            filepath=str(out_fbx),
            use_selection=True,
            object_types={"ARMATURE", "MESH"},
            apply_scale_options="FBX_SCALE_ALL",
            axis_forward="-Y",
            axis_up="Z",
            use_space_transform=False,
            add_leaf_bones=False,
            mesh_smooth_type="FACE",
            bake_anim=False,
        )
        print(f"[✓] Exported Vehicle FBX: {out_fbx}")

    # Render Gate 2 Vehicle SBS vs UM_01_alt
    bpy.ops.wm.obj_import(filepath=str(UM_OBJ_01))
    um_alt = bpy.context.selected_objects[0]
    um_alt.name = "UM_REF_01_Gate2"
    um_alt.location = (4.5, 0.0, 0.0)
    tank.location = (-4.5, 0.0, 0.0)
    clay = bpy.data.materials.new("UM_Alt_Clay")
    clay.use_nodes = True
    clay.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.76, 0.80, 0.88, 1.0)
    um_alt.data.materials.clear()
    um_alt.data.materials.append(clay)

    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = (o not in (tank, um_alt))

    scene = bpy.context.scene
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 860
    if not scene.camera:
        cd = bpy.data.cameras.new("G2VhCam")
        cam = bpy.data.objects.new("G2VhCam", cd)
        scene.collection.objects.link(cam)
        scene.camera = cam
    else:
        cam = scene.camera
    if not any(o.type == "LIGHT" for o in scene.objects):
        for nm, eng, loc in [("Key", 1800, (-8, -14, 15)), ("Fill", 900, (10, -12, 8)), ("Rim", 1100, (0, 12, 14))]:
            ld = bpy.data.lights.new(nm, type="AREA")
            ld.energy = eng
            ld.size = 6.0
            lo = bpy.data.objects.new(nm, ld)
            scene.collection.objects.link(lo)
            lo.location = Vector(loc)
            lo.rotation_euler = (Vector((0, 0, 2)) - lo.location).to_track_quat("-Z", "Y").to_euler()

    cam.location = Vector((8.5, -22.0, 10.5))
    cam.data.lens = 42
    cam.rotation_euler = (Vector((0.0, 0.0, 2.2)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(SCRATCH_DIR / "gate2_tarn_vehicle_vs_um.png")
    bpy.ops.render.render(write_still=True)
    print("[OK] Phase 3 Vehicle Rigging + Gate 2 Vehicle Render complete!")


if __name__ == "__main__":
    main()
