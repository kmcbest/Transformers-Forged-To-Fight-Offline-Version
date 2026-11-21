import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
BLENDER_EXE = ROOT / "toolchain" / "blender" / "blender.exe"
BLEND_FILE = ROOT / "3rd-party-models" / "Sideswipe" / "01_aligned_mesh" / "sideswipe_robot_aligned.blend"
TEX_DIR = ROOT / "3rd-party-models" / "Sideswipe" / "02_textures"
SCRATCH_RAW = ROOT / "3rd-party-models" / "Sideswipe" / "sideswipe_portrait_raw.png"
OUT_DIR = ROOT / "assets_redeco"


def blender_render():
    import bpy
    from mathutils import Vector
    import numpy as np

    print("=== [Blender] Rendering Sideswipe Bust Portrait ===")
    bpy.ops.wm.open_mainfile(filepath=str(BLEND_FILE))

    # Reset any parent offsets
    for o in bpy.data.objects:
        if o.name.startswith("Barricade") or "Donor" in o.name:
            bpy.data.objects.remove(o, do_unlink=True)

    arm = bpy.data.objects.get("ARM_Sideswipe_Robot")
    if arm:
        arm.location = Vector((0.0, 0.0, 0.0))
        arm.rotation_euler = Vector((0.0, 0.0, 0.0))

    robot = bpy.data.objects.get("cha_sideswipe_main")
    assert robot is not None, "Sideswipe robot mesh not found in blend file"
    robot.location = Vector((0.0, 0.0, 0.0))

    # Set up sleek silver metallic PBR shader with atlased textures
    mat = bpy.data.materials.new("MAT_Sideswipe_Portrait")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Metallic"].default_value = 0.85
    bsdf.inputs["Roughness"].default_value = 0.30
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    diff_path = TEX_DIR / "cha_sideswipe_main_Diffuse.png"
    if diff_path.exists():
        tex_d = nt.nodes.new("ShaderNodeTexImage")
        tex_d.image = bpy.data.images.load(str(diff_path))
        nt.links.new(tex_d.outputs["Color"], bsdf.inputs["Base Color"])

    norm_path = TEX_DIR / "cha_sideswipe_main_Normal_unity.png"
    if not norm_path.exists():
        norm_path = TEX_DIR / "cha_sideswipe_main_Normal.png"
    if norm_path.exists():
        tex_n = nt.nodes.new("ShaderNodeTexImage")
        tex_n.image = bpy.data.images.load(str(norm_path))
        tex_n.image.colorspace_settings.name = "Non-Color"
        nrm_map = nt.nodes.new("ShaderNodeNormalMap")
        nrm_map.inputs["Strength"].default_value = 1.0
        nt.links.new(tex_n.outputs["Color"], nrm_map.inputs["Color"])
        nt.links.new(nrm_map.outputs["Normal"], bsdf.inputs["Normal"])

    em_path = TEX_DIR / "cha_sideswipe_main_Emission.png"
    if em_path.exists():
        tex_e = nt.nodes.new("ShaderNodeTexImage")
        tex_e.image = bpy.data.images.load(str(em_path))
        nt.links.new(tex_e.outputs["Color"], bsdf.inputs["Emission"])
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 3.0

    robot.data.materials.clear()
    robot.data.materials.append(mat)
    robot.hide_render = False
    robot.hide_viewport = False
    for poly in robot.data.polygons:
        poly.material_index = 0

    for o in bpy.data.objects:
        if o.type == "MESH" and o != robot:
            o.hide_render = True

    # Evaluate bounds
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
    print(f"Sideswipe bbox: X=[{min(xs):.3f},{max(xs):.3f}], Y=[{min(ys):.3f},{max(ys):.3f}], Z=[{min_z:.3f},{max_z:.3f}], H={h:.3f}")

    # Camera target at head & chest (Z ~ 85% of height, ~9.2m)
    target = Vector((cx, cy, min_z + h * 0.85))
    cam_dist = h * 0.65
    # 3/4 angle: slightly to the right, in front (-Y in Blender), looking at head/chest
    cam_pos = Vector((cx + h * 0.18, cy - cam_dist, min_z + h * 0.88))

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
    scene.view_settings.look = "High Contrast"

    for o in list(scene.objects):
        if o.type == "LIGHT":
            bpy.data.objects.remove(o, do_unlink=True)

    # Sleek Autobot Heroic Studio Lighting (Bright silver highlights + subtle warm/cool accents)
    light_specs = [
        ("Key_Silver", 16.0 * (h ** 2), 0.35 * h, (cx + h * 0.45, cy - h * 0.65, min_z + h * 1.10), (1.0, 0.98, 0.96)),
        ("Fill_Cyan", 7.0 * (h ** 2), 0.55 * h, (cx - h * 0.60, cy - h * 0.50, min_z + h * 0.85), (0.70, 0.88, 1.0)),
        ("Rim_Red", 15.0 * (h ** 2), 0.35 * h, (cx - h * 0.40, cy + h * 0.50, min_z + h * 1.05), (1.0, 0.30, 0.25)),
        ("Rim_White", 12.0 * (h ** 2), 0.30 * h, (cx + h * 0.45, cy + h * 0.40, min_z + h * 1.15), (0.95, 0.98, 1.0)),
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
    cd.lens = 50.0
    cam = bpy.data.objects.new("PortraitCam", cd)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.location = cam_pos
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()

    SCRATCH_RAW.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(SCRATCH_RAW)
    bpy.ops.render.render(write_still=True)
    print(f"[✓] Rendered raw Sideswipe portrait to {SCRATCH_RAW}")


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

    S = 1024
    c_x0, c_x1 = 19 * 4, 237 * 4
    c_y0, c_y1 = 42 * 4, 1024
    bev = 16

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

    # Autobot heroic combat backdrop (rich ruby red / fiery crimson glow)
    yy, xx = np.mgrid[0:S, 0:S]
    dx = (xx - 512.0) / 440.0
    dy = (yy - 360.0) / 520.0
    rad = np.clip(1.0 - np.sqrt(dx * dx + dy * dy), 0.0, 1.0) ** 1.35
    vert = np.clip((yy - c_y0) / float(c_y1 - c_y0), 0.0, 1.0)
    r = np.clip(110 + 130 * rad - 35 * vert, 25, 245).astype(np.uint8)
    g = np.clip(18 + 45 * rad - 12 * vert, 5, 85).astype(np.uint8)
    b = np.clip(22 + 40 * rad - 15 * vert, 5, 80).astype(np.uint8)
    bg_rgb = np.stack([r, g, b, np.array(mask)], axis=-1)
    card = Image.fromarray(bg_rgb, "RGBA")

    # Trim / scale character so crest sits at y ~ 20 and bust fills card
    subj_h = max(1, 1024 - y_top)
    scale = (1024 - 20) / subj_h
    new_w = int(round(raw.width * scale))
    new_h = int(round(raw.height * scale))
    scaled = raw.resize((new_w, new_h), Image.Resampling.LANCZOS)

    cx_subj = 0.5 * (x_min + x_max) * scale
    paste_x = int(round(512 - cx_subj))
    paste_y = int(round(20 - y_top * scale))

    fg = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    fg.paste(scaled, (paste_x, paste_y), scaled)

    # Pop-out clipping: top of head breaks out, sides clipped to card
    fg_arr = np.array(fg)
    below_top = yy >= (c_y0 + bev)
    outside_x = (xx < c_x0) | (xx > c_x1)
    fg_arr[below_top & outside_x, 3] = 0
    fg = Image.fromarray(fg_arr, "RGBA")

    comp = Image.alpha_composite(card, fg)

    # Bottom vignette
    comp_arr = np.array(comp).astype(np.float32)
    vig = np.clip((yy - 820.0) / 204.0, 0.0, 1.0) ** 1.4
    shade = 1.0 - 0.75 * vig[:, :, None]
    comp_arr[:, :, :3] *= shade
    comp = Image.fromarray(np.clip(comp_arr, 0, 255).astype(np.uint8), "RGBA")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p256 = comp.resize((256, 256), Image.Resampling.LANCZOS).filter(ImageFilter.UnsharpMask(radius=0.8, percent=55, threshold=2))

    # Save 256x256 card portraits and dialogue icons
    targets_256 = [
        "portrait_sideswipe_cin_rotf_large.png",
        "portrait_sideswipe_cin_rotf_quest.png",
        "sideswipe_cin_rotf.png",
    ]
    for name in targets_256:
        p256.save(OUT_DIR / name, format="PNG")
        print(f"[✓] Saved {name} (256x256 RGBA)")

    # Small 128x128 RGB headshot
    full_bg = np.stack([r, g, b, np.full_like(r, 255)], axis=-1)
    small_comp = Image.alpha_composite(Image.fromarray(full_bg, "RGBA"), fg)
    crop_box = (int(S * 0.12), int(S * 0.02), int(S * 0.88), int(S * 0.78))
    p128 = small_comp.crop(crop_box).resize((128, 128), Image.Resampling.LANCZOS).convert("RGB")
    targets_128 = [
        "portrait_sideswipe_cin_rotf_small.jpg",
    ]
    for name in targets_128:
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
    print("[*] Launching Blender portrait render for Sideswipe...")
    subprocess.run(cmd, check=True)
    composite_portraits()


if __name__ == "__main__":
    main()
