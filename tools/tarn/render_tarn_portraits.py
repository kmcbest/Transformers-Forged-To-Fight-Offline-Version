#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_tarn_portraits.py
Generates official TFTF-style portraits and dialogue icons for Tarn (tarn_gs) in assets_redeco/:
  - portrait_tarn_gs_large.png / portrait_tarn_large.png (256x256 RGBA pop-out card)
  - portrait_tarn_gs_quest.png / portrait_tarn_quest.png (256x256 RGBA pop-out card)
  - tarn_gs.png / tarn.png (256x256 RGBA dialogue icon)
  - portrait_tarn_gs_small.jpg / portrait_tarn_small.jpg (128x128 RGB tight headshot)
"""
import sys
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(r"E:\Agent\TFTF-blender")
BLENDER_EXE = ROOT / "toolchain" / "blender" / "blender.exe"
RIGGED_BLEND = ROOT / "3rd-party-models" / "Tarn" / "06_working" / "tarn_rigged_um53.blend"
TEX_DIR = ROOT / "3rd-party-models" / "Tarn" / "06_working" / "unified_textures"
SCRATCH_RAW = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\66aaeff3-2652-4f24-8fc9-00b0ef375582\scratch\tarn_portrait_raw.png")
OUT_DIR = ROOT / "assets_redeco"


def blender_render():
    import bpy
    from mathutils import Vector

    bpy.ops.wm.open_mainfile(filepath=str(RIGGED_BLEND))
    robot = bpy.data.objects.get("Tarn_Robot_LowPoly")
    assert robot is not None, "Tarn_Robot_LowPoly not found in blend"

    # Build clean PBR shader using unified textures
    mat = bpy.data.materials.new("MAT_Tarn_Portrait")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Metallic"].default_value = 0.25
    bsdf.inputs["Roughness"].default_value = 0.42
    bsdf.inputs["Emission Strength"].default_value = 1.6
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    tex_a = nt.nodes.new("ShaderNodeTexImage")
    tex_a.image = bpy.data.images.load(str(TEX_DIR / "cha_tarn_main_a.png"))
    nt.links.new(tex_a.outputs["Color"], bsdf.inputs["Base Color"])

    tex_n = nt.nodes.new("ShaderNodeTexImage")
    tex_n.image = bpy.data.images.load(str(TEX_DIR / "cha_tarn_main_NM_std.png"))
    tex_n.image.colorspace_settings.name = "Non-Color"
    nrm_map = nt.nodes.new("ShaderNodeNormalMap")
    nrm_map.inputs["Strength"].default_value = 0.85
    nt.links.new(tex_n.outputs["Color"], nrm_map.inputs["Color"])
    nt.links.new(nrm_map.outputs["Normal"], bsdf.inputs["Normal"])

    tex_e = nt.nodes.new("ShaderNodeTexImage")
    tex_e.image = bpy.data.images.load(str(TEX_DIR / "cha_tarn_main_Emission.png"))
    nt.links.new(tex_e.outputs["Color"], bsdf.inputs["Emission"])

    robot.data.materials.clear()
    robot.data.materials.append(mat)
    robot.hide_render = False
    robot.hide_viewport = False
    for o in bpy.data.objects:
        if o.type == "MESH" and o != robot:
            o.hide_render = True

    # Pose arms slightly downward / hero stance if armature exists
    arm = robot.parent if robot.parent and robot.parent.type == "ARMATURE" else None
    if arm:
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode="POSE")
        for bname, rot_deg in [
            ("LeftShoulder", (0.0, 0.0, 8.0)),
            ("RightShoulder", (0.0, 0.0, -8.0)),
            ("LeftArm", (8.0, 0.0, 14.0)),
            ("RightArm", (8.0, 0.0, -14.0)),
            ("LeftForeArm", (24.0, 0.0, 0.0)),
            ("RightForeArm", (24.0, 0.0, 0.0)),
            ("Spine1", (0.0, 0.0, 6.0)),
            ("Head", (-4.0, 0.0, -8.0)),
        ]:
            pb = arm.pose.bones.get(bname)
            if pb:
                import math
                pb.rotation_mode = "XYZ"
                pb.rotation_euler = (math.radians(rot_deg[0]), math.radians(rot_deg[1]), math.radians(rot_deg[2]))
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.view_layer.update()

    # Evaluate world-space mesh bounds after pose
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = robot.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    mw = eval_obj.matrix_world
    zs = [(mw @ v.co).z for v in mesh.vertices]
    xs = [(mw @ v.co).x for v in mesh.vertices]
    ys = [(mw @ v.co).y for v in mesh.vertices]
    eval_obj.to_mesh_clear()

    min_z, max_z = min(zs), max(zs)
    h = max_z - min_z
    cx = 0.5 * (min(xs) + max(xs))
    cy = 0.5 * (min(ys) + max(ys))
    print(f"Tarn evaluated bbox: X=[{min(xs):.3f},{max(xs):.3f}], Y=[{min(ys):.3f},{max(ys):.3f}], Z=[{min_z:.3f},{max_z:.3f}], H={h:.3f}")

    # Upper bust framing target (include full helmet crest & back turret tips cleanly inside top margin)
    target = Vector((cx, cy, min_z + h * 0.78))
    cam_dist = h * 0.70
    cam_pos = Vector((cx + h * 0.18, cy - cam_dist, min_z + h * 0.83))

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 64
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look = "Medium High Contrast"

    # Remove old lights and build studio dramatic portrait rig (purple rim + balanced key)
    for o in list(scene.objects):
        if o.type == "LIGHT":
            bpy.data.objects.remove(o, do_unlink=True)

    light_specs = [
        ("Key", 14.0 * (h ** 2), 0.45 * h, (cx + h * 0.55, cy - h * 0.80, min_z + h * 1.15), (1.0, 0.96, 0.94)),
        ("Fill", 5.5 * (h ** 2), 0.65 * h, (cx - h * 0.70, cy - h * 0.65, min_z + h * 0.80), (0.68, 0.55, 1.0)),
        ("RimPurple", 18.0 * (h ** 2), 0.40 * h, (cx - h * 0.45, cy + h * 0.55, min_z + h * 1.15), (0.85, 0.25, 1.0)),
        ("RimWhite", 12.0 * (h ** 2), 0.35 * h, (cx + h * 0.50, cy + h * 0.45, min_z + h * 1.10), (0.95, 0.90, 1.0)),
    ]
    for nm, energy, sz, loc, col in light_specs:
        ld = bpy.data.lights.new(nm, type="AREA")
        ld.energy = energy
        ld.size = sz
        ld.color = col
        lo = bpy.data.objects.new(nm, ld)
        scene.collection.objects.link(lo)
        lo.location = Vector(loc)
        lo.rotation_euler = (target - lo.location).to_track_quat("-Z", "Y").to_euler()

    cd = bpy.data.cameras.new("PortraitCam")
    cd.lens = 58.0
    cam = bpy.data.objects.new("PortraitCam", cd)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.location = cam_pos
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()

    SCRATCH_RAW.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(SCRATCH_RAW)
    bpy.ops.render.render(write_still=True)
    print(f"[✓] Rendered raw portrait to {SCRATCH_RAW}")


def composite_portraits():
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter

    raw = Image.open(SCRATCH_RAW).convert("RGBA")
    arr = np.array(raw)
    alpha = arr[:, :, 3]
    ys, xs = np.where(alpha > 20)
    assert len(ys) > 100, "Raw portrait render appears empty!"
    y_top = int(ys.min())
    y_bot = int(ys.max())
    x_min, x_max = int(xs.min()), int(xs.max())
    print(f"Raw subject bbox: x=[{x_min},{x_max}], y=[{y_top},{y_bot}] on {raw.size}")

    # Build 1024x1024 portrait card matching TFTF large/quest layout:
    # At 256x256: card body spans x=[19..236], y=[42..255] with 4px top bevels
    S = 1024
    c_x0, c_x1 = 19 * 4, 237 * 4
    c_y0, c_y1 = 42 * 4, 1024
    bev = 16

    card = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    mask = Image.new("L", (S, S), 0)
    mdraw = ImageDraw.Draw(mask)
    poly = [
        (c_x0 + bev, c_y0),
        (c_x1 - bev, c_y0),
        (c_x1, c_y0 + bev),
        (c_x1, c_y1),
        (c_x0, c_y1),
        (c_x0, c_y0 + bev),
    ]
    mdraw.polygon(poly, fill=255)

    # Rich Decepticon purple backdrop inside the card
    yy, xx = np.mgrid[0:S, 0:S]
    dx = (xx - 512.0) / 440.0
    dy = (yy - 360.0) / 520.0
    rad = np.clip(1.0 - np.sqrt(dx * dx + dy * dy), 0.0, 1.0) ** 1.35
    vert = np.clip((yy - c_y0) / float(c_y1 - c_y0), 0.0, 1.0)
    r = np.clip(28 + 108 * rad - 18 * vert, 10, 180).astype(np.uint8)
    g = np.clip(10 + 26 * rad - 8 * vert, 6, 80).astype(np.uint8)
    b = np.clip(48 + 150 * rad - 28 * vert, 18, 225).astype(np.uint8)
    bg_rgb = np.stack([r, g, b, np.array(mask)], axis=-1)
    card = Image.fromarray(bg_rgb, "RGBA")

    # Trim / place character so head/turret tips sit at y ~ 24 (6px at 256) and bust fills card cleanly
    subj_h = max(1, 1024 - y_top)  # measure from top of subject down to bottom of image
    scale = (1024 - 24) / subj_h
    new_w = int(round(raw.width * scale))
    new_h = int(round(raw.height * scale))
    scaled = raw.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Position scaled render so head/turret top sits at y=24 and bust stays horizontally centered
    cx_subj = 0.5 * (x_min + x_max) * scale
    paste_x = int(round(512 - cx_subj))
    paste_y = int(round(24 - y_top * scale))

    fg = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    fg.paste(scaled, (paste_x, paste_y), scaled)

    # Below y=42*4, clip foreground strictly inside card horizontal sides, while keeping pop-out above top border!
    fg_arr = np.array(fg)
    below_top = yy >= (c_y0 + bev)
    outside_x = (xx < c_x0) | (xx > c_x1)
    fg_arr[below_top & outside_x, 3] = 0
    fg = Image.fromarray(fg_arr, "RGBA")

    comp = Image.alpha_composite(card, fg)

    # Smooth dark vignette near bottom edge of card (y = 840..1024) inside opaque pixels
    comp_arr = np.array(comp).astype(np.float32)
    vig = np.clip((yy - 820.0) / 204.0, 0.0, 1.0) ** 1.4
    shade = 1.0 - 0.72 * vig[:, :, None]
    comp_arr[:, :, :3] *= shade
    comp = Image.fromarray(np.clip(comp_arr, 0, 255).astype(np.uint8), "RGBA")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p256 = comp.resize((256, 256), Image.Resampling.LANCZOS).filter(ImageFilter.UnsharpMask(radius=0.8, percent=55, threshold=2))
    for name in [
        "portrait_tarn_gs_large.png",
        "portrait_tarn_large.png",
        "portrait_tarn_gs_quest.png",
        "portrait_tarn_quest.png",
        "tarn_gs.png",
        "tarn.png",
    ]:
        p256.save(OUT_DIR / name, format="PNG")
        print(f"[✓] Saved {name} (256x256 RGBA)")

    # Small portrait 128x128 RGB on full Decepticon purple backdrop (no transparent frame corners)
    full_bg = np.stack([r, g, b, np.full_like(r, 255)], axis=-1)
    small_comp = Image.alpha_composite(Image.fromarray(full_bg, "RGBA"), fg)
    # Slight tighter crop around upper head/chest for clarity at 128x128
    crop_box = (int(S * 0.10), int(S * 0.02), int(S * 0.90), int(S * 0.82))
    p128 = small_comp.crop(crop_box).resize((128, 128), Image.Resampling.LANCZOS).convert("RGB")
    for name in ["portrait_tarn_gs_small.jpg", "portrait_tarn_small.jpg"]:
        p128.save(OUT_DIR / name, format="JPEG", quality=93)
        print(f"[✓] Saved {name} (128x128 RGB)")


def main():
    if "--blender-render" in sys.argv:
        blender_render()
        return

    cmd = [
        str(BLENDER_EXE),
        "-b",
        "--python-exit-code", "1",
        "--python", str(Path(__file__).resolve()),
        "--", "--blender-render",
    ]
    print(f"[*] Launching Blender portrait render...")
    res = subprocess.run(cmd, check=True)
    composite_portraits()


if __name__ == "__main__":
    main()
