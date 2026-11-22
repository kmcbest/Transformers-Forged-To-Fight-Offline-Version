import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
from mathutils import Vector
from pathlib import Path

print("=== [Swindle] Gate 1 & 2 Master Vehicle Pipeline (FOC -> 2048 Atlas -> RootBone Aligned) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
TEX_DIR = ROOT / "3rd-party-models" / "Swindle" / "02_textures"
ALIGNED_DIR = ROOT / "3rd-party-models" / "Swindle" / "01_aligned_mesh"
FBX_OUT_DIR = ROOT / "3rd-party-models" / "Swindle" / "03_fbx_exports"
UNITY_SWINDLE_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Swindle"
RENDERS_DIR = ROOT / "renders" / "swindle"

for d in (ALIGNED_DIR, FBX_OUT_DIR, UNITY_SWINDLE_DIR, RENDERS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# 4-Quadrant Vehicle Atlas Boxes (u_scale, u_off, v_scale, v_off)
VEH_UV_MAP = {
    "VH_Swindle_Cust_E_Mat_INST":   (0.5, 0.0, 0.5, 0.5),
    "RB_Swindle_Wheel_INST":        (0.5, 0.0, 0.5, 0.0),
    "TR_FactionLogo_Mat_INST.003":  (0.5, 0.5, 0.5, 0.0),
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
    mat = bpy.data.materials.new("M_Swindle_Vh")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    ta = nt.nodes.new("ShaderNodeTexImage")
    ta.image = bpy.data.images.load(str(TEX_DIR / "cha_swindle_tform_misc_Diffuse.png"))
    nt.links.new(ta.outputs["Color"], bsdf.inputs["Base Color"])

    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = bpy.data.images.load(str(TEX_DIR / "cha_swindle_tform_misc_Normal_unity.png"))
    tn.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])

    te = nt.nodes.new("ShaderNodeTexImage")
    te.image = bpy.data.images.load(str(TEX_DIR / "cha_swindle_tform_misc_Emission.png"))
    nt.links.new(te.outputs["Color"], bsdf.inputs["Emission"])
    bsdf.inputs["Emission Strength"].default_value = 2.5
    bsdf.inputs["Roughness"].default_value = 0.62
    bsdf.inputs["Metallic"].default_value = 0.25
    return mat


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=FBX_PATH)

    veh = bpy.data.objects.get("Collection.dmx")
    assert veh is not None, "Missing Collection.dmx!"

    for o in list(bpy.data.objects):
        if o != veh:
            bpy.data.objects.remove(o, do_unlink=True)

    bpy.ops.object.select_all(action="DESELECT")
    veh.select_set(True)
    bpy.context.view_layer.objects.active = veh
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    veh.modifiers.clear()
    if veh.data.shape_keys:
        veh.shape_key_clear()
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    veh.name = "cha_swindle_gs_01"

    # Remap UVs
    remap_uvs_clean(veh, VEH_UV_MAP)

    # In raw FBX, Collection.dmx:
    # Front is +X, Left is +Y, Up is +Z
    # Rotating R_z(-90): Left=+X, Forward=-Y, Up=+Z (det=+1)
    xs = [v.co.x for v in veh.data.vertices]
    ys = [v.co.y for v in veh.data.vertices]
    zs = [v.co.z for v in veh.data.vertices]
    x_center = 0.5 * (min(xs) + max(xs))
    y_center = 0.5 * (min(ys) + max(ys))
    z_min = min(zs)

    # Scale: raw length = 4.07m -> 8.55m => Scale = 2.10
    SCALE_VEH = 2.10

    for v in veh.data.vertices:
        xr = (v.co.x - x_center) * SCALE_VEH
        yr = (v.co.y - y_center) * SCALE_VEH
        zr = (v.co.z - z_min) * SCALE_VEH
        v.co.x = yr      # Y_raw (Left) -> +X
        v.co.y = -xr     # X_raw (Front) -> -Y (Forward)
        v.co.z = zr      # Z_raw (Up) -> +Z
    veh.data.update()

    xs_b = [v.co.x for v in veh.data.vertices]
    ys_b = [v.co.y for v in veh.data.vertices]
    zs_b = [v.co.z for v in veh.data.vertices]
    print(f"[Bounds] Vehicle Blender space: X=[{min(xs_b):.3f},{max(xs_b):.3f}] (width={max(xs_b)-min(xs_b):.2f})")
    print(f"                                Y=[{min(ys_b):.3f},{max(ys_b):.3f}] (length={max(ys_b)-min(ys_b):.2f})")
    print(f"                                Z=[{min(zs_b):.3f},{max(zs_b):.3f}] (height={max(zs_b)-min(zs_b):.2f})")

    # Build clean Armature matching Wheeljack vehicle root bone: chop2_torso_main_center
    arm_d = bpy.data.armatures.new("ARM_Swindle_Veh_Data")
    v_arm = bpy.data.objects.new("ARM_Swindle_Veh", arm_d)
    bpy.context.scene.collection.objects.link(v_arm)
    bpy.context.view_layer.objects.active = v_arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_d.edit_bones.new("chop2_torso_main_center")
    eb.head = Vector((0, 0, 1.23))
    eb.tail = Vector((0, -1.0, 1.23))

    eb_cog = arm_d.edit_bones.new("COG")
    eb_cog.head = Vector((0, 0, 0))
    eb_cog.tail = Vector((0, -1.0, 0))
    bpy.ops.object.mode_set(mode="OBJECT")

    veh.vertex_groups.clear()
    vg_root = veh.vertex_groups.new(name="chop2_torso_main_center")
    vg_root.add(list(range(len(veh.data.vertices))), 1.0, "REPLACE")

    veh.parent = v_arm
    mod = veh.modifiers.new("Armature", "ARMATURE")
    mod.object = v_arm

    veh.data.materials.clear()
    mat_v = make_veh_preview_material()
    veh.data.materials.append(mat_v)
    for poly in veh.data.polygons:
        poly.material_index = 0

    bpy.ops.object.select_all(action="DESELECT")
    veh.select_set(True)
    v_arm.select_set(True)
    bpy.context.view_layer.objects.active = v_arm
    for fbx_out in (FBX_OUT_DIR / "swindle_veh_prepared.fbx", UNITY_SWINDLE_DIR / "swindle_veh_prepared.fbx"):
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
    print(f"[✓] Exported Prepared Vehicle FBX: {UNITY_SWINDLE_DIR / 'swindle_veh_prepared.fbx'}")
    bpy.ops.wm.save_as_mainfile(filepath=str(ALIGNED_DIR / "swindle_veh_aligned.blend"))


if __name__ == "__main__":
    main()
