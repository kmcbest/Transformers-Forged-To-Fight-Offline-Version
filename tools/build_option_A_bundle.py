import os
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps, ImageFilter
import UnityPy

def create_option_A_bundle():
    print("=== Generating Bumblebee Option A Bundle ===")
    
    tex_path = r"E:\Agent\TFTF-blender\tools\bumblebee_cin\cha_bumblebee_cin_dotm_main_a.png"
    orig_img = Image.open(tex_path).convert("RGBA")
    w, h = orig_img.size

    with open(r"E:\Agent\TFTF-blender\tools\true_forehead_uvs.json", "r") as f:
        uv_polys = json.load(f)

    # Filter strictly for Cluster 2 (x >= 0.25 in UV space: the forehead dome, NOT the square blocks)
    c2_polys = [p for p in uv_polys if (sum(pt[0] for pt in p) / len(p)) >= 0.25]
    print(f"Cluster 2 polygons (forehead dome only): {len(c2_polys)}")

    # 1. Create Diffuse Texture for Option A
    mask_c2 = Image.new("L", (w, h), 0)
    draw_c2 = ImageDraw.Draw(mask_c2)
    for p in c2_polys:
        pts = [(pt[0] * w, (1.0 - pt[1]) * h) for pt in p]
        draw_c2.polygon(pts, fill=255)

    # Slight dilation (1 pixel) to cover seam edges
    mask_c2_dilated = mask_c2.filter(ImageFilter.MaxFilter(3))

    diffuse_optA = orig_img.copy()
    orig_rgb = orig_img.convert("RGB")
    pixels = diffuse_optA.load()
    orig_pixels = orig_rgb.load()
    mask_pixels = mask_c2_dilated.load()

    ty_r, ty_g, ty_b = 248, 178, 10

    for x in range(w):
        for y in range(h):
            m = mask_pixels[x, y]
            if m > 0:
                r, g, b = orig_pixels[x, y]
                gray = (r * 0.299 + g * 0.587 + b * 0.114) / 200.0
                gray = min(1.2, max(0.4, gray))
                
                new_r = min(255, int(ty_r * gray))
                new_g = min(255, int(ty_g * gray))
                new_b = min(255, int(ty_b * gray))
                
                alpha = m / 255.0
                curr_r, curr_g, curr_b, curr_a = pixels[x, y]
                out_r = int(curr_r * (1 - alpha) + new_r * alpha)
                out_g = int(curr_g * (1 - alpha) + new_g * alpha)
                out_b = int(curr_b * (1 - alpha) + new_b * alpha)
                pixels[x, y] = (out_r, out_g, out_b, curr_a)

    out_diffuse_path = r"E:\Agent\TFTF-blender\tools\bee_tex_optA_strict.png"
    diffuse_optA.save(out_diffuse_path)
    print("Saved diffuse:", out_diffuse_path)

    # 2. Create RAOE for Option A
    raoe_path = r"E:\Agent\TFTF-blender\tools\bumblebee_cin\main_tform_misc_RAOE.png"
    raoe_img = Image.open(raoe_path).convert("RGBA")
    rw, rh = raoe_img.size
    raoe_mask = mask_c2_dilated.resize((rw, rh), Image.Resampling.LANCZOS)
    raoe_pixels = raoe_img.load()
    rmask_pixels = raoe_mask.load()

    for x in range(rw):
        for y in range(rh):
            m = rmask_pixels[x, y]
            if m > 50:
                alpha = (m / 255.0) * 0.9
                r, g, b, a = raoe_pixels[x, y]
                new_r = int(r * (1 - alpha) + 32 * alpha)
                new_g = int(g * (1 - alpha) + 202 * alpha)
                raoe_pixels[x, y] = (new_r, new_g, b, a)

    out_raoe_path = r"E:\Agent\TFTF-blender\tools\bee_raoe_optA_strict.png"
    raoe_img.save(out_raoe_path)
    print("Saved RAOE:", out_raoe_path)

    # 3. Patch AssetBundle
    src_bundle = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\bumblebee_cin_dotm_odr\bumblebee_cin_dotm.assetbundle"
    out_dir = Path(r"E:\Agent\TFTF-blender\assets_redeco")
    out_dir.mkdir(exist_ok=True)
    out_bundle_A = out_dir / "bumblebee_cin_dotm_optionA.assetbundle"

    env = UnityPy.load(src_bundle)
    replaced_count = 0

    for obj in env.objects:
        if obj.type.name == "Texture2D":
            data = obj.read()
            if data.m_Name == "cha_bumblebee_cin_dotm_main_a":
                data.image = diffuse_optA
                data.save()
                replaced_count += 1
            elif data.m_Name == "main_tform_misc_RAOE":
                data.image = raoe_img
                data.save()
                replaced_count += 1

    print(f"Replaced {replaced_count} textures.")
    with open(out_bundle_A, "wb") as f:
        f.write(env.file.save(packer="lz4"))
    
    print(f"Saved Option A bundle to: {out_bundle_A} (Size: {os.path.getsize(out_bundle_A)} bytes)")

    # Also backup current option B bundle if not already backed up
    curr_bundle = out_dir / "bumblebee_cin_dotm.assetbundle"
    backup_bundle_B = out_dir / "bumblebee_cin_dotm_optionB.assetbundle"
    if curr_bundle.exists() and not backup_bundle_B.exists():
        import shutil
        shutil.copy2(curr_bundle, backup_bundle_B)
        print(f"Backed up current Option B bundle to: {backup_bundle_B}")

if __name__ == "__main__":
    create_option_A_bundle()
