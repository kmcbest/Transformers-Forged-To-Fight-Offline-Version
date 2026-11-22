import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
from mathutils import Vector, Matrix
from pathlib import Path

print("=== [Blast Off] Gate 2 Master Vehicle Pipeline (FOC Space Shuttle -> 2048 Atlas -> Megatronus RootBone Aligned) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
DONOR_JET_OBJ = ROOT / "3rd-party-models" / "BlastOff" / "00_donor_reference" / "cha_megatronus_gs_kabam_01_jet.obj"
TEX_DIR = ROOT / "3rd-party-models" / "BlastOff" / "02_textures"
ALIGNED_DIR = ROOT / "3rd-party-models" / "BlastOff" / "01_aligned_mesh"
FBX_OUT_DIR = ROOT / "3rd-party-models" / "BlastOff" / "03_fbx_exports"
UNITY_BLASTOFF_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "BlastOff"
RENDERS_DIR = ROOT / "renders" / "blastoff"

for d in (ALIGNED_DIR, FBX_OUT_DIR, UNITY_BLASTOFF_DIR, RENDERS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# 2048 Vehicle Atlas UV boxes: (u_scale, u_off, v_scale, v_off)
VEH_UV_MAP = {
    "VH_Blastoff_Cust_MatINST":    (0.5,  0.0, 0.5,  0.5),   # (0, 0, 1024, 1024) in PIL
    "TR_FactionLogo_Mat_INST.001": (0.25, 0.0, 0.25, 0.25),  # (0, 1024, 512, 512) in PIL
}


def remap_uvs_clean(obj, uv_map, default_box=(0.5, 0.0, 0.5, 0.5)):
    uv_layer = obj.data.uv_layers.active
    assert uv_layer is not None, "Vehicle missing active UV layer!"
    mat_slots = [slot.material.name if slot.material else "" for slot in obj.material_slots]
    repaired = 0
    for poly in obj.data.polygons:
        mname = mat_slots[poly.material_index] if poly.material_index < len(mat_slots) else ""
        u_sc, u_off, v_sc, v_off = uv_map.get(mname, default_box)

        pts = []
        for li in poly.loop_indices:
            uv = uv_layer.data[li].uv
            bad = (not math.isfinite(uv.x)) or (not math.isfinite(uv.y)) or abs(uv.x) > 10.0 or abs(uv.y) > 10.0
            if bad:
                repaired += 1
                pts.append((li, 0.5, 0.5))
            else:
                pts.append((li, uv.x, uv.y))

        mu = sum(p[1] for p in pts) / len(pts)
        mv = sum(p[2] for p in pts) / len(pts)
        du = math.floor(mu)
        dv = math.floor(mv)

        for li, ux, vy in pts:
            u_loc = min(0.994, max(0.006, ux - du))
            v_loc = min(0.994, max(0.006, vy - dv))
            uv_layer.data[li].uv = (u_loc * u_sc + u_off, v_loc * v_sc + v_off)
    obj.data.update()
    print(f"[✓] Remapped Vehicle UVs cleanly into 2048 Atlas (repaired corrupt loops={repaired}).")


def make_veh_preview_material():
    mat = bpy.data.materials.new("M_BlastOff_Vh")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    ta = nt.nodes.new("ShaderNodeTexImage")
    ta.image = bpy.data.images.load(str(TEX_DIR / "cha_blastoff_tform_misc_Diffuse.png"))
    nt.links.new(ta.outputs["Color"], bsdf.inputs["Base Color"])

    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = bpy.data.images.load(str(TEX_DIR / "cha_blastoff_tform_misc_Normal_unity.png"))
    tn.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])

    te = nt.nodes.new("ShaderNodeTexImage")
    te.image = bpy.data.images.load(str(TEX_DIR / "cha_blastoff_tform_misc_Emission.png"))
    nt.links.new(te.outputs["Color"], bsdf.inputs["Emission"])
    bsdf.inputs["Emission Strength"].default_value = 2.5
    bsdf.inputs["Roughness"].default_value = 0.58
    bsdf.inputs["Metallic"].default_value = 0.35
    return mat


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    print(f"[*] Importing FBX from {FBX_PATH}...")
    bpy.ops.import_scene.fbx(filepath=FBX_PATH)

    veh_mesh_names = [
        "VH_Blastoff_SKEL.mo.dmx",
        "VH_BlastoffWing_STAT.mo.001.dmx",
        "VH_BlastoffWing_STAT.mo.dmx",
    ]

    veh_objs = [bpy.data.objects.get(n) for n in veh_mesh_names if n in bpy.data.objects]
    assert len(veh_objs) == 3, f"Expected 3 vehicle mesh objects, found {[o.name for o in veh_objs]}"

    # Isolate vehicle objects
    keep_set = set(veh_objs)
    for o in list(bpy.data.objects):
        if o not in keep_set:
            bpy.data.objects.remove(o, do_unlink=True)

    # Apply parent transform and clear modifiers
    for obj in veh_objs:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        if obj.data.shape_keys:
            obj.shape_key_clear()
        bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
        obj.modifiers.clear()
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Remap per-polygon UVs
    for obj in veh_objs:
        remap_uvs_clean(obj, VEH_UV_MAP)

    # Join the 3 vehicle parts into single object
    bpy.ops.object.select_all(action="DESELECT")
    for obj in veh_objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = veh_objs[0]
    bpy.ops.object.join()
    veh = bpy.context.active_object
    veh.name = "cha_blastoff_gs_01"

    # Analyze raw bounding box
    xs_raw = [v.co.x for v in veh.data.vertices]
    ys_raw = [v.co.y for v in veh.data.vertices]
    zs_raw = [v.co.z for v in veh.data.vertices]

    x_tail = min(xs_raw)      # ~3.842
    x_nose = max(xs_raw)      # ~10.120
    raw_length = x_nose - x_tail # ~6.279
    y_center = 0.5 * (min(ys_raw) + max(ys_raw)) # ~ -10.0145
    z_bottom = min(zs_raw)    # ~0.131

    # Megatronus jet target dimensions:
    # Unity: Length = 10.277m (Z from -4.239 to +6.039), Height = 3.886m
    # Blender space: Y from +4.239 (tail) to -6.039 (nose), Ground Z = 0.000m
    SCALE_FACTOR = 1.0  # Preserve 1.0x native Megatronus vehicle bounds
    TARGET_LENGTH = 10.277 * SCALE_FACTOR
    SCALE_VEH = TARGET_LENGTH / raw_length

    print(f"[*] Raw Vehicle Length: {raw_length:.3f}m -> Scaled to {TARGET_LENGTH:.3f}m (Scale={SCALE_VEH:.4f}x, factor={SCALE_FACTOR}x)")

    # Coordinate transformation into Blender space (Left=+X, Forward=-Y, Up=+Z, det=+1)
    for v in veh.data.vertices:
        ox = v.co.x
        oy = v.co.y
        oz = v.co.z
        # Y_raw (Left/Right) -> +X (Left=+X, Right=-X)
        v.co.x = (oy - y_center) * SCALE_VEH
        # X_raw (Nose=+X, Tail=-X) -> -Y (Nose=-Y, Tail=+Y)
        v.co.y = - (ox - x_tail) * SCALE_VEH + 4.239 * SCALE_FACTOR
        # Z_raw (Up=+Z) -> +Z (Grounded at Z=0.000m)
        v.co.z = (oz - z_bottom) * SCALE_VEH

    veh.data.update()

    xs_b = [v.co.x for v in veh.data.vertices]
    ys_b = [v.co.y for v in veh.data.vertices]
    zs_b = [v.co.z for v in veh.data.vertices]
    print(f"[Bounds] Vehicle in Blender space:")
    print(f"  X (Wingspan): [{min(xs_b):.3f}, {max(xs_b):.3f}] (width={max(xs_b)-min(xs_b):.2f}m)")
    print(f"  Y (Length):   [{min(ys_b):.3f}, {max(ys_b):.3f}] (length={max(ys_b)-min(ys_b):.2f}m)")
    print(f"  Z (Height):   [{min(zs_b):.3f}, {max(zs_b):.3f}] (height={max(zs_b)-min(zs_b):.2f}m, min_z={min(zs_b):.3f}m)")

    # Build clean Armature matching Megatronus vehicle root bone: Reference/COG/chop1_torso_center
    arm_d = bpy.data.armatures.new("ARM_BlastOff_Veh_Data")
    v_arm = bpy.data.objects.new("ARM_BlastOff_Veh", arm_d)
    bpy.context.scene.collection.objects.link(v_arm)
    bpy.context.view_layer.objects.active = v_arm
    bpy.ops.object.mode_set(mode="EDIT")

    # Root bone chop1_torso_center located at Megatronus bindpose coordinate (0.036, 2.119, 2.443) * SCALE_FACTOR
    eb_root = arm_d.edit_bones.new("chop1_torso_center")
    eb_root.head = Vector((0.036 * SCALE_FACTOR, 2.119 * SCALE_FACTOR, 2.443 * SCALE_FACTOR))
    eb_root.tail = Vector((0.036 * SCALE_FACTOR, 1.119 * SCALE_FACTOR, 2.443 * SCALE_FACTOR))

    eb_cog = arm_d.edit_bones.new("COG")
    eb_cog.head = Vector((0.0, 0.0, 0.0))
    eb_cog.tail = Vector((0.0, -1.0, 0.0))
    eb_root.parent = eb_cog

    bpy.ops.object.mode_set(mode="OBJECT")

    # Weight all vertices 1.0 to chop1_torso_center
    veh.vertex_groups.clear()
    vg_root = veh.vertex_groups.new(name="chop1_torso_center")
    vg_root.add(list(range(len(veh.data.vertices))), 1.0, "REPLACE")

    veh.parent = v_arm
    mod = veh.modifiers.new("Armature", "ARMATURE")
    mod.object = v_arm

    # Assign preview material
    veh.data.materials.clear()
    mat_v = make_veh_preview_material()
    veh.data.materials.append(mat_v)
    for poly in veh.data.polygons:
        poly.material_index = 0

    # Render Side-by-Side Verification with Megatronus Jet
    print("=== Rendering Gate 2 Side-by-Side Comparison for Vehicle Mode ===")
    if DONOR_JET_OBJ.exists():
        bpy.ops.wm.obj_import(filepath=str(DONOR_JET_OBJ))
        host_jet = bpy.context.selected_objects[0]
        host_jet.name = "Megatronus_Jet_Reference"
        # Megatronus jet is oriented with +Z as forward in Unity, imported into Blender:
        # Check and place host jet to the left (-X in Blender)
        host_jet.location.x = -8.5

        cam_data = bpy.data.cameras.new("Gate2_Jet_Camera")
        cam_data.lens = 35.0
        cam_obj = bpy.data.objects.new("Gate2_Jet_Camera", cam_data)
        bpy.context.collection.objects.link(cam_obj)
        # Position camera in front-quarter view (-Y, elevated +Z)
        cam_obj.location = (-4.25, -22.0, 10.0)
        cam_obj.rotation_euler = (math.radians(65), 0, 0)
        bpy.context.scene.camera = cam_obj

        # Add key sun lighting
        light_data = bpy.data.lights.new("Gate2_Jet_Sun", "SUN")
        light_data.energy = 3.5
        light_obj = bpy.data.objects.new("Gate2_Jet_Sun", light_data)
        bpy.context.collection.objects.link(light_obj)
        light_obj.rotation_euler = (math.radians(45), math.radians(25), 0)

        bpy.context.scene.render.resolution_x = 1920
        bpy.context.scene.render.resolution_y = 1080
        out_render = RENDERS_DIR / "gate2_blender_jet_sbs.png"
        bpy.context.scene.render.filepath = str(out_render)
        bpy.ops.render.render(write_still=True)
        print(f"[✓] Rendered Gate 2 Jet Side-by-Side: {out_render}")

        bpy.data.objects.remove(host_jet, do_unlink=True)
        bpy.data.objects.remove(cam_obj, do_unlink=True)
        bpy.data.objects.remove(light_obj, do_unlink=True)

    # Export FBX for Gate 2 validation and Unity import
    bpy.ops.object.select_all(action="DESELECT")
    veh.select_set(True)
    v_arm.select_set(True)
    bpy.context.view_layer.objects.active = v_arm

    for fbx_out in (
        FBX_OUT_DIR / "blastoff_vh_prepared.fbx",
        UNITY_BLASTOFF_DIR / "blastoff_vh_prepared.fbx",
        FBX_OUT_DIR / "blastoff_jet_prepared.fbx",
        UNITY_BLASTOFF_DIR / "blastoff_jet_prepared.fbx",
    ):
        bpy.ops.export_scene.fbx(
            filepath=str(fbx_out),
            use_selection=True,
            object_types={"ARMATURE", "MESH"},
            apply_scale_options="FBX_SCALE_ALL",
            axis_forward="-Z",
            axis_up="Y",
            add_leaf_bones=False,
            bake_anim=False,
        )
        print(f"[✓] Exported Prepared Vehicle FBX: {fbx_out}")

    bpy.ops.wm.save_as_mainfile(filepath=str(ALIGNED_DIR / "blastoff_jet_aligned.blend"))
    print(f"[✓] Saved Blender project: {ALIGNED_DIR / 'blastoff_jet_aligned.blend'}")


if __name__ == "__main__":
    main()
