import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
from mathutils import Vector
from pathlib import Path

print("=== [Brawl] Gate 1 & 2 Master Tank Pipeline (FOC -> 2048 Atlas -> COG Aligned) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
TEX_DIR = ROOT / "3rd-party-models" / "Brawl" / "02_textures"
ALIGNED_DIR = ROOT / "3rd-party-models" / "Brawl" / "01_aligned_mesh"
FBX_OUT_DIR = ROOT / "3rd-party-models" / "Brawl" / "03_fbx_exports"
UNITY_BRAWL_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Brawl"
RENDERS_DIR = ROOT / "renders" / "brawl"

for d in (ALIGNED_DIR, FBX_OUT_DIR, UNITY_BRAWL_DIR, RENDERS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# 4-Quadrant Tank Atlas Boxes (u_scale, u_off, v_scale, v_off)
TANK_UV_MAP = {
    "VH_Brawl_Cust_MatINST":        (0.5, 0.0, 0.5, 0.5),
    "VH_BrawLegsl_Cust_MatINST":    (0.5, 0.5, 0.5, 0.5),
    "VH_BrawInterior_Cust_MatINST": (0.5, 0.0, 0.5, 0.0),
    "TR_FactionLogo_Mat_INST":      (0.5, 0.5, 0.5, 0.0),
}


def remap_uvs_clean(obj, uv_map, default_box=(0.5, 0.0, 0.5, 0.5)):
    uv_layer = obj.data.uv_layers.active
    assert uv_layer is not None, "Tank missing active UV layer!"
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
    print(f"[✓] Remapped Tank UVs cleanly into 2048 Atlas (repaired corrupt loops={repaired}).")


def make_tank_preview_material():
    mat = bpy.data.materials.new("M_Brawl_Vh")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    ta = nt.nodes.new("ShaderNodeTexImage")
    ta.image = bpy.data.images.load(str(TEX_DIR / "cha_brawl_tform_misc_Diffuse.png"))
    nt.links.new(ta.outputs["Color"], bsdf.inputs["Base Color"])

    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = bpy.data.images.load(str(TEX_DIR / "cha_brawl_tform_misc_Normal_unity.png"))
    tn.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])

    te = nt.nodes.new("ShaderNodeTexImage")
    te.image = bpy.data.images.load(str(TEX_DIR / "cha_brawl_tform_misc_Emission.png"))
    nt.links.new(te.outputs["Color"], bsdf.inputs["Emission"])
    bsdf.inputs["Emission Strength"].default_value = 2.5
    bsdf.inputs["Roughness"].default_value = 0.62
    bsdf.inputs["Metallic"].default_value = 0.25
    return mat


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=FBX_PATH)

    tank = bpy.data.objects.get("VH_BrawlCINE_SKEL.001.dmx")
    assert tank is not None, "Missing VH_BrawlCINE_SKEL.001.dmx!"
    for o in list(bpy.data.objects):
        if o != tank:
            bpy.data.objects.remove(o, do_unlink=True)

    bpy.ops.object.select_all(action="DESELECT")
    tank.select_set(True)
    bpy.context.view_layer.objects.active = tank
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    tank.modifiers.clear()
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    tank.name = "cha_brawl_gs_01"

    # Remap UVs BEFORE consolidating materials!
    remap_uvs_clean(tank, TANK_UV_MAP)

    # Rotate + scale into Blender Standard Space:
    # FOC: +X=Front (cannon tip at max X), +Y=Left (sym about -19.62), +Z=Up
    # Blender Standard (det=+1): Left=+X, Forward=-Y, Up=+Z  => B_x = y_raw, B_y = -x_raw, B_z = z_raw
    xs = [v.co.x for v in tank.data.vertices]
    ys = [v.co.y for v in tank.data.vertices]
    zs = [v.co.z for v in tank.data.vertices]
    x_center = 0.5 * (min(xs) + max(xs))
    y_center = 0.5 * (min(ys) + max(ys))
    z_min = min(zs)
    SCALE_TANK = 1.15

    # Verify which end is cannon barrel (+X vs -X): turret high verts Z > 1.8
    hi_xs = [v.co.x for v in tank.data.vertices if v.co.z > 1.5]
    print(f"Tank raw turret/cannon X center={sum(hi_xs)/len(hi_xs):.3f}, hull center={x_center:.3f}, max_x={max(xs):.3f}, min_x={min(xs):.3f}")

    for v in tank.data.vertices:
        xr = (v.co.x - x_center) * SCALE_TANK
        yr = (v.co.y - y_center) * SCALE_TANK
        zr = (v.co.z - z_min) * SCALE_TANK
        v.co.x = yr
        v.co.y = -xr
        v.co.z = zr
    tank.data.update()

    xs_b = [v.co.x for v in tank.data.vertices]
    ys_b = [v.co.y for v in tank.data.vertices]
    zs_b = [v.co.z for v in tank.data.vertices]
    print(f"[Bounds] Tank Blender space: X=[{min(xs_b):.3f},{max(xs_b):.3f}] Y=[{min(ys_b):.3f},{max(ys_b):.3f}] Z=[{min(zs_b):.3f},{max(zs_b):.3f}]")

    # Recalculate clean smooth normals (preserving sharp edge splits if needed)
    # Create clean COG armature matching Donor vehicle bone name "COG"
    arm_d = bpy.data.armatures.new("ARM_Brawl_Tank_Data")
    t_arm = bpy.data.objects.new("ARM_Brawl_Tank", arm_d)
    bpy.context.scene.collection.objects.link(t_arm)
    bpy.context.view_layer.objects.active = t_arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_d.edit_bones.new("COG")
    eb.head = Vector((0, 0, 0))
    eb.tail = Vector((0, -1.0, 0))
    bpy.ops.object.mode_set(mode="OBJECT")

    tank.vertex_groups.clear()
    vg_cog = tank.vertex_groups.new(name="COG")
    vg_cog.add(list(range(len(tank.data.vertices))), 1.0, "REPLACE")

    tank.parent = t_arm
    mod = tank.modifiers.new("Armature", "ARMATURE")
    mod.object = t_arm

    tank.data.materials.clear()
    mat_t = make_tank_preview_material()
    tank.data.materials.append(mat_t)
    for poly in tank.data.polygons:
        poly.material_index = 0

    bpy.ops.object.select_all(action="DESELECT")
    tank.select_set(True)
    t_arm.select_set(True)
    bpy.context.view_layer.objects.active = t_arm
    for fbx_out in (FBX_OUT_DIR / "brawl_tank_prepared.fbx", UNITY_BRAWL_DIR / "brawl_tank_prepared.fbx"):
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
    print(f"[✓] Exported Prepared Tank FBX: {UNITY_BRAWL_DIR / 'brawl_tank_prepared.fbx'}")
    bpy.ops.wm.save_as_mainfile(filepath=str(ALIGNED_DIR / "brawl_tank_aligned.blend"))

    # Render Gate 1 Preview (Tank 3/4 view + Robot imported alongside for 2-up clean view!)
    bpy.ops.wm.append(
        filepath=str(ALIGNED_DIR / "brawl_robot_aligned.blend" / "Object" / "cha_brawl_gs_00"),
        directory=str(ALIGNED_DIR / "brawl_robot_aligned.blend" / "Object"),
        filename="cha_brawl_gs_00",
    )
    rob = bpy.data.objects.get("cha_brawl_gs_00")
    if rob:
        rob.location = (-5.0, 0.0, 0.0)
    t_arm.location = (5.0, 0.0, 0.0)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.12, 0.13, 0.16, 1.0)
        bg.inputs[1].default_value = 0.8

    for lx, ly, lz, energy in [(8, -14, 14, 3500), (-8, -12, 10, 2200), (0, 14, 10, 1800)]:
        ld = bpy.data.lights.new("L", type="POINT")
        ld.energy = energy
        lo = bpy.data.objects.new("Light", ld)
        lo.location = (lx, ly, lz)
        scene.collection.objects.link(lo)

    cam_d = bpy.data.cameras.new("Cam")
    cam_d.lens = 42
    cam = bpy.data.objects.new("Cam", cam_d)
    cam.location = (2.5, -24.0, 7.5)
    direction = Vector((0.0, 0.0, 4.5)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(cam)
    scene.camera = cam

    out_png = RENDERS_DIR / "gate1_blender_preview.png"
    scene.render.filepath = str(out_png)
    bpy.ops.render.render(write_still=True)
    print(f"[✓] Rendered Gate 1 Blender Robot + Tank Preview: {out_png}")


if __name__ == "__main__":
    main()
