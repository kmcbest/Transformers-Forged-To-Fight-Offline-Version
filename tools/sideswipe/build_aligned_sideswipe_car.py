import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
import json
import math
from mathutils import Vector
from pathlib import Path

print("=== [Sideswipe] Stage 2: Master Vehicle Pipeline (FBX -> 2048 Atlas -> BodyBase Rigged FBX) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
CAR_FBX = ROOT / "3rd-party-models" / "Sideswipe" / "01_source" / "Sideswipe_Car.fbx"
DONOR_OBJ = ROOT / "3rd-party-models" / "Sideswipe" / "00_donor_reference" / "cha_barricade_cin_dotm_01_car.obj"
TEX_DIR = ROOT / "3rd-party-models" / "Sideswipe" / "02_textures"
ALIGNED_DIR = ROOT / "3rd-party-models" / "Sideswipe" / "01_aligned_mesh"
FBX_OUT_DIR = ROOT / "3rd-party-models" / "Sideswipe" / "03_fbx_exports"
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Sideswipe"
RENDERS_DIR = ROOT / "renders" / "sideswipe"

for d in (ALIGNED_DIR, FBX_OUT_DIR, UNITY_DIR, RENDERS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# 4-Quadrant Vehicle UV Atlas mapping (u_scale, u_offset, v_scale, v_offset)
# OpenGL UV: V=0 is bottom, V=1 is top
# Q0 (Top-Left): Car Body & Glass -> (0.5, 0.0, 0.5, 0.5)
# Q1 (Top-Right): Car Interior    -> (0.5, 0.5, 0.5, 0.5)
# Q2 (Bottom-Left): Wheels        -> (0.5, 0.0, 0.5, 0.0)
CAR_UV_MAP = {
    "Car":    (0.5, 0.0, 0.5, 0.5),
    "Glass":  (0.5, 0.0, 0.5, 0.5),
    "Int":    (0.5, 0.5, 0.5, 0.5),
    "Wheels": (0.5, 0.0, 0.5, 0.0),
}


def remap_uvs_clean(obj, uv_map, default_box=(0.5, 0.0, 0.5, 0.5)):
    uv_layer = obj.data.uv_layers.active
    if uv_layer is None:
        if len(obj.data.uv_layers) > 0:
            uv_layer = obj.data.uv_layers[0]
            obj.data.uv_layers.active = uv_layer
        else:
            uv_layer = obj.data.uv_layers.new(name="UVMap")
    mat_slots = [slot.material.name if slot.material else "" for slot in obj.material_slots]
    for poly in obj.data.polygons:
        mname = mat_slots[poly.material_index] if poly.material_index < len(mat_slots) else ""
        u_sc, u_off, v_sc, v_off = uv_map.get(mname, default_box)

        pts = []
        for li in poly.loop_indices:
            uv = uv_layer.data[li].uv
            ux = 0.5 if (not math.isfinite(uv.x) or abs(uv.x) > 10.0) else uv.x
            vy = 0.5 if (not math.isfinite(uv.y) or abs(uv.y) > 10.0) else uv.y
            pts.append((li, ux, vy))

        mu = sum(p[1] for p in pts) / len(pts)
        mv = sum(p[2] for p in pts) / len(pts)
        du = math.floor(mu)
        dv = math.floor(mv)

        for li, ux, vy in pts:
            u_loc = min(0.992, max(0.008, ux - du))
            v_loc = min(0.992, max(0.008, vy - dv))
            uv_layer.data[li].uv = (u_loc * u_sc + u_off, v_loc * v_sc + v_off)
    obj.data.update()
    print("[✓] Remapped vehicle UVs cleanly into 4-quadrant atlas.")


def make_car_preview_material():
    mat = bpy.data.materials.new("M_Sideswipe_Vh")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    ta = nt.nodes.new("ShaderNodeTexImage")
    ta.image = bpy.data.images.load(str(TEX_DIR / "cha_sideswipe_tform_misc_Diffuse.png"))
    nt.links.new(ta.outputs["Color"], bsdf.inputs["Base Color"])

    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = bpy.data.images.load(str(TEX_DIR / "cha_sideswipe_tform_misc_Normal_unity.png"))
    tn.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])

    te = nt.nodes.new("ShaderNodeTexImage")
    te.image = bpy.data.images.load(str(TEX_DIR / "cha_sideswipe_tform_misc_Emission.png"))
    nt.links.new(te.outputs["Color"], bsdf.inputs["Emission"])
    bsdf.inputs["Emission Strength"].default_value = 2.5
    bsdf.inputs["Roughness"].default_value = 0.50
    bsdf.inputs["Metallic"].default_value = 0.40
    return mat


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(CAR_FBX))

    mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
    arm = bpy.data.objects.get("Root")
    if arm and arm.type == 'ARMATURE':
        bpy.data.objects.remove(arm, do_unlink=True)

    for o in mesh_objs:
        o.modifiers.clear()
        o.parent = None

    bpy.ops.object.select_all(action='DESELECT')
    for o in mesh_objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objs[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Remap UVs BEFORE joining meshes so material slots are preserved
    for o in mesh_objs:
        remap_uvs_clean(o, CAR_UV_MAP)

    # Join into single car object
    bpy.ops.object.select_all(action='DESELECT')
    for o in mesh_objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objs[0]
    bpy.ops.object.join()
    car = bpy.context.active_object
    car.name = "cha_sideswipe_vh"

    # Raw FBX coordinates:
    # X = Left / Right
    # Y = Height (Up) [0, 40.8]
    # Z = Length: Front hood is -Z, Rear exhaust is +Z
    #
    # Transform to Blender Standard (det = +1, Front is -Y):
    # X_blender = -X  (rotates 180 around Up to point Front to -Y)
    # Y_blender = Z   (Front hood is -Y)
    # Z_blender = Y   (Up is +Z, Ground is Z=0)
    #
    # Scale to length ~11.20m matching Barricade car (11.29m)
    for v in car.data.vertices:
        rx, ry, rz = v.co.x, v.co.y, v.co.z
        v.co.x = -rx
        v.co.y = rz
        v.co.z = ry
    car.data.update()

    xs = [v.co.x for v in car.data.vertices]
    ys = [v.co.y for v in car.data.vertices]
    zs = [v.co.z for v in car.data.vertices]
    z_min = min(zs)
    raw_len = max(ys) - min(ys)
    SCALE_CAR = 11.20 / raw_len

    for v in car.data.vertices:
        v.co.z -= z_min
        v.co.x *= SCALE_CAR
        v.co.y *= SCALE_CAR
        v.co.z *= SCALE_CAR
    car.data.update()

    xs_b = [v.co.x for v in car.data.vertices]
    ys_b = [v.co.y for v in car.data.vertices]
    zs_b = [v.co.z for v in car.data.vertices]
    print(f"[Bounds] Vehicle Blender space: X=[{min(xs_b):.3f},{max(xs_b):.3f}] Y=[{min(ys_b):.3f},{max(ys_b):.3f}] Z=[{min(zs_b):.3f},{max(zs_b):.3f}]")

    # Build clean Armature with BodyBase bone (matching Barricade's root bone)
    arm_d = bpy.data.armatures.new("ARM_Sideswipe_Vh_Data")
    v_arm = bpy.data.objects.new("ARM_Sideswipe_Vh", arm_d)
    bpy.context.scene.collection.objects.link(v_arm)
    bpy.context.view_layer.objects.active = v_arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_d.edit_bones.new("BodyBase")
    eb.head = Vector((0, 0, 0))
    eb.tail = Vector((0, -1.0, 0))
    bpy.ops.object.mode_set(mode="OBJECT")

    car.vertex_groups.clear()
    vg_bb = car.vertex_groups.new(name="BodyBase")
    vg_bb.add(list(range(len(car.data.vertices))), 1.0, "REPLACE")

    car.parent = v_arm
    mod = car.modifiers.new("Armature", "ARMATURE")
    mod.object = v_arm

    car.data.materials.clear()
    mat_v = make_car_preview_material()
    car.data.materials.append(mat_v)
    for poly in car.data.polygons:
        poly.material_index = 0

    # Export FBX
    bpy.ops.object.select_all(action="DESELECT")
    car.select_set(True)
    v_arm.select_set(True)
    bpy.context.view_layer.objects.active = v_arm

    for fbx_out in (FBX_OUT_DIR / "sideswipe_vh_prepared.fbx", UNITY_DIR / "sideswipe_vh_prepared.fbx"):
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
    print(f"[✓] Exported Prepared Vehicle FBX: {UNITY_DIR / 'sideswipe_vh_prepared.fbx'}")
    bpy.ops.wm.save_as_mainfile(filepath=str(ALIGNED_DIR / "sideswipe_vh_aligned.blend"))

    # Render Gate 2 Blender Vehicle Side-by-Side Comparison (Barricade Car OBJ + Sideswipe Car)
    bpy.ops.wm.obj_import(filepath=str(DONOR_OBJ))
    donor_car = bpy.context.selected_objects[0]
    donor_car.name = "Barricade_Car_Donor_Ref"

    # Place side-by-side: Barricade at X = -5.0, Sideswipe at X = +5.0
    donor_car.location = (-5.0, 0.0, 0.0)
    v_arm.location = (5.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.12, 0.13, 0.16, 1.0)
        bg.inputs[1].default_value = 0.8

    for lx, ly, lz, energy in [(8, -14, 12, 3500), (-8, -14, 10, 2200), (0, 14, 10, 1800)]:
        ld = bpy.data.lights.new("L", type="POINT")
        ld.energy = energy
        lo = bpy.data.objects.new("Light", ld)
        lo.location = (lx, ly, lz)
        scene.collection.objects.link(lo)

    cam_d = bpy.data.cameras.new("Cam")
    cam_d.lens = 38
    cam = bpy.data.objects.new("Cam", cam_d)
    cam.location = (0.0, -22.0, 8.5)
    direction = Vector((0.0, 0.0, 1.5)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(cam)
    scene.camera = cam

    out_car_sbs = RENDERS_DIR / "gate2_blender_car_sbs.png"
    scene.render.filepath = str(out_car_sbs)
    bpy.ops.render.render(write_still=True)
    print(f"[✓] Rendered Gate 2 Blender Vehicle SBS: {out_car_sbs}")


if __name__ == "__main__":
    main()
