import os
import sys
import math
import bpy
from mathutils import Vector

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BLEND_PATH = r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\06_working\tarn_workspace_cleaned.blend"
UM_REF_DIR = r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\04_donor_reference\ultramagnus_gs_leader"
SCRATCH_DIR = r"C:\Users\Xiangli496\.gemini\antigravity\brain\66aaeff3-2652-4f24-8fc9-00b0ef375582\scratch"


def clear_refs():
    for o in list(bpy.data.objects):
        if o.name.startswith("UM_REF_") or o.name.startswith("TMP_Cam") or o.name.startswith("Gate1Cam"):
            bpy.data.objects.remove(o, do_unlink=True)


def import_obj_clean(path, name):
    bpy.ops.wm.obj_import(filepath=path)
    obj = bpy.context.selected_objects[0]
    obj.name = name
    # Unity -> Blender orientation on exported OBJ? Let's inspect raw OBJ coords!
    return obj


def world_bbox(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    zs = [p.z for p in pts]
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
    clear_refs()

    tarn_bot = bpy.data.objects.get("Tarn_Robot_LowPoly")
    tarn_vh_objs = [o for o in bpy.data.objects if o.name.startswith("TarnTank")]
    meg_ref = bpy.data.objects.get("REF_cha_megatron_gs_leader2015_00")

    um00 = import_obj_clean(os.path.join(UM_REF_DIR, "cha_ultramagnus_gs_leader_00_robot.obj"), "UM_REF_00")
    um01 = import_obj_clean(os.path.join(UM_REF_DIR, "cha_ultramagnus_gs_leader_01_alt.obj"), "UM_REF_01")
    um_axe = import_obj_clean(os.path.join(UM_REF_DIR, "cha_ultramagnus_gs_leader_wpns_axe_right.obj"), "UM_REF_axe")
    um_gunr = import_obj_clean(os.path.join(UM_REF_DIR, "cha_ultramagnus_gs_leader_wpns_gun_right.obj"), "UM_REF_gunr")
    um_gunl = import_obj_clean(os.path.join(UM_REF_DIR, "cha_ultramagnus_gs_leader_wpns_pistol_left.obj"), "UM_REF_gunl")

    for o in (um00, um01, um_axe, um_gunr, um_gunl):
        # Verify how REF_cha_megatron_gs_leader2015_00 was imported: bpy.ops.wm.obj_import defaults Y-up -> Z-up (rot_x=90)
        bx, by, bz = world_bbox(o)
        print(f"{o.name:16s} raw bbox: X=[{bx[0]:.3f},{bx[1]:.3f}] Y=[{by[0]:.3f},{by[1]:.3f}] Z=[{bz[0]:.3f},{bz[1]:.3f}]")

    # Apply same white clay material as REF_cha_megatron_gs_leader2015_00 if needed
    clay = bpy.data.materials.new("UM_Clay")
    clay.use_nodes = True
    bsdf = clay.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.78, 0.82, 0.90, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.55
    for o in (um00, um01, um_axe, um_gunr, um_gunl):
        o.data.materials.clear()
        o.data.materials.append(clay)

    # Render 1: Tarn_Robot_LowPoly (X=-3.5) vs UM_REF_00 (X=+3.8) + weapons
    tarn_bot.hide_render = False
    if meg_ref:
        meg_ref.hide_render = True
    for o in tarn_vh_objs:
        o.hide_render = True
    um01.hide_render = True
    um00.hide_render = False
    um_axe.hide_render = False
    um_gunr.hide_render = False
    um_gunl.hide_render = False

    tarn_bot.location = (-3.6, 0.0, 0.0)
    um00.location = (3.8, 0.0, 0.0)
    um_axe.location = (3.8, 0.0, 0.0)
    # Place gunr/gunl near origin offset just to see size
    um_gunr.location = (1.0, 0.0, 6.0)
    um_gunl.location = (6.5, 0.0, 6.0)

    cam_data = bpy.data.cameras.new("TMP_Cam")
    cam_data.lens = 45
    cam = bpy.data.objects.new("TMP_Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    def aim_cam(loc, target):
        cam.location = Vector(loc)
        d = Vector(target) - cam.location
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 860

    aim_cam((0.1, -24.0, 7.5), (0.1, 0.0, 7.0))
    scene.render.filepath = os.path.join(SCRATCH_DIR, "um_vs_tarn_robot.png")
    bpy.ops.render.render(write_still=True)

    # Render 2: Tarn_Vehicle vs UM_REF_01 alt mode
    tarn_bot.hide_render = True
    um00.hide_render = True
    um_axe.hide_render = True
    um_gunr.hide_render = True
    um_gunl.hide_render = True
    um01.hide_render = False
    for o in tarn_vh_objs:
        o.hide_render = False
        o.location.x += -4.0

    # Report Tarn_Vehicle combined bbox
    pts = []
    for o in tarn_vh_objs:
        pts.extend([o.matrix_world @ Vector(c) for c in o.bound_box])
    print(
        f"Tarn_Vehicle shifted(-4) bbox: X=[{min(p.x for p in pts):.3f},{max(p.x for p in pts):.3f}] "
        f"Y=[{min(p.y for p in pts):.3f},{max(p.y for p in pts):.3f}] Z=[{min(p.z for p in pts):.3f},{max(p.z for p in pts):.3f}]"
    )
    um01.location = (4.0, 0.0, 0.0)
    aim_cam((8.0, -24.0, 12.0), (0.0, 0.0, 2.5))
    scene.render.filepath = os.path.join(SCRATCH_DIR, "um_vs_tarn_alt.png")
    bpy.ops.render.render(write_still=True)
    print("Done rendering UM vs Tarn comparisons.")


if __name__ == "__main__":
    main()
