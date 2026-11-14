import os
import sys
from pathlib import Path
import bpy
from mathutils import Vector

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BAKED_BLEND = r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\06_working\tarn_workspace_baked.blend"
TEX_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\06_working\unified_textures")
SCRATCH_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\66aaeff3-2652-4f24-8fc9-00b0ef375582\scratch")


def main():
    bpy.ops.wm.open_mainfile(filepath=BAKED_BLEND)
    robot = bpy.data.objects.get("Tarn_Robot_LowPoly")
    assert robot is not None

    # Print vertex group counts summary (handL__, handR__, part__)
    vg_counts = {vg.index: 0 for vg in robot.vertex_groups}
    for v in robot.data.vertices:
        for g in v.groups:
            if g.weight > 0.01:
                vg_counts[g.group] = vg_counts.get(g.group, 0) + 1
    print(f"Tarn_Robot_LowPoly: verts={len(robot.data.vertices)}, polys={len(robot.data.polygons)}, vgs={len(robot.vertex_groups)}")
    for vg in robot.vertex_groups:
        c = vg_counts.get(vg.index, 0)
        if vg.name.startswith("handL__") or vg.name.startswith("handR__") or c == 0:
            print(f"  VG '{vg.name:28s}': {c:5d} verts")

    # Apply unified 2048x2048 baked preview material
    mat = bpy.data.materials.new("MAT_Tarn_Unified_Preview")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    tex_a = nt.nodes.new("ShaderNodeTexImage")
    tex_a.image = bpy.data.images.load(str(TEX_DIR / "cha_tarn_main_a.png"))
    nt.links.new(tex_a.outputs["Color"], bsdf.inputs["Base Color"])

    tex_n = nt.nodes.new("ShaderNodeTexImage")
    tex_n.image = bpy.data.images.load(str(TEX_DIR / "cha_tarn_main_NM_std.png"))
    tex_n.image.colorspace_settings.name = "Non-Color"
    nrm_map = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex_n.outputs["Color"], nrm_map.inputs["Color"])
    nt.links.new(nrm_map.outputs["Normal"], bsdf.inputs["Normal"])

    tex_e = nt.nodes.new("ShaderNodeTexImage")
    tex_e.image = bpy.data.images.load(str(TEX_DIR / "cha_tarn_main_Emission.png"))
    nt.links.new(tex_e.outputs["Color"], bsdf.inputs["Emission"])
    bsdf.inputs["Emission Strength"].default_value = 3.0
    bsdf.inputs["Roughness"].default_value = 0.55

    robot.data.materials.clear()
    robot.data.materials.append(mat)
    robot.hide_render = False
    for o in bpy.data.objects:
        if o.type == "MESH" and o != robot:
            o.hide_render = True

    scene = bpy.context.scene
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024

    if not scene.camera:
        cd = bpy.data.cameras.new("PreviewCam")
        cam = bpy.data.objects.new("PreviewCam", cd)
        scene.collection.objects.link(cam)
        scene.camera = cam
    else:
        cam = scene.camera

    # Ensure lighting exists
    if not any(o.type == "LIGHT" for o in scene.objects):
        for nm, eng, loc in [("Key", 1800, (-8, -14, 15)), ("Fill", 900, (10, -12, 8)), ("Rim", 1100, (0, 12, 14))]:
            ld = bpy.data.lights.new(nm, type="AREA")
            ld.energy = eng
            ld.size = 6.0
            lo = bpy.data.objects.new(nm, ld)
            scene.collection.objects.link(lo)
            lo.location = Vector(loc)
            lo.rotation_euler = (Vector((0, 0, 6)) - lo.location).to_track_quat("-Z", "Y").to_euler()

    def render(loc, target, fname):
        cam.location = Vector(loc)
        cam.data.lens = 50
        cam.rotation_euler = (Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(SCRATCH_DIR / fname)
        bpy.ops.render.render(write_still=True)

    render((0.0, -18.5, 6.4), (0.0, 0.0, 6.2), "phase2_baked_robot_front.png")
    render((0.0, -7.2, 9.6), (0.0, 0.0, 9.5), "phase2_baked_robot_head_chest.png")


if __name__ == "__main__":
    main()
