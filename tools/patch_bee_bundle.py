import os
import sys
from pathlib import Path
import UnityPy
from PIL import Image

def patch_bee(opt="A"):
    src_bundle = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\bumblebee_cin_dotm_odr\bumblebee_cin_dotm.assetbundle"
    out_dir = Path(r"E:\Agent\TFTF-blender\assets_redeco")
    out_dir.mkdir(exist_ok=True)
    out_bundle = out_dir / "bumblebee_cin_dotm.assetbundle"

    diffuse_path = r"E:\Agent\TFTF-blender\tools\bee_tex_optA.png" if opt == "A" else r"E:\Agent\TFTF-blender\tools\bee_tex_optB.png"
    
    print(f"Patching Bumblebee bundle with Option {opt} ({diffuse_path})...")
    diffuse_img = Image.open(diffuse_path)

    # Also prepare updated RAOE
    raoe_path = r"E:\Agent\TFTF-blender\tools\bumblebee_cin\main_tform_misc_RAOE.png"
    raoe_img = Image.open(raoe_path).convert("RGBA")
    
    # Update RAOE for forehead:
    # Forehead plate in RAOE (half res 512x512) around x=180..215, y=10..45
    # Smooth car clearcoat: Roughness=32, Gloss/Spec=202
    mask_path = r"E:\Agent\TFTF-blender\tools\forehead_mask.png"
    mask_img = Image.open(mask_path).resize((512, 512), Image.Resampling.LANCZOS)
    raoe_pixels = raoe_img.load()
    mask_pixels = mask_img.load()
    for x in range(512):
        for y in range(512):
            m = mask_pixels[x, y]
            if m > 50:
                # Lerp towards car clearcoat (32, 202, 0, 255)
                alpha = (m / 255.0) * 0.9
                r, g, b, a = raoe_pixels[x, y]
                new_r = int(r * (1 - alpha) + 32 * alpha)
                new_g = int(g * (1 - alpha) + 202 * alpha)
                raoe_pixels[x, y] = (new_r, new_g, b, a)

    env = UnityPy.load(src_bundle)
    replaced_count = 0

    for obj in env.objects:
        if obj.type.name == "Texture2D":
            data = obj.read()
            if data.m_Name == "cha_bumblebee_cin_dotm_main_a":
                print(f"  Replacing {data.m_Name} ({data.m_Width}x{data.m_Height})")
                data.image = diffuse_img
                data.save()
                replaced_count += 1
            elif data.m_Name == "main_tform_misc_RAOE":
                print(f"  Replacing {data.m_Name} ({data.m_Width}x{data.m_Height})")
                data.image = raoe_img
                data.save()
                replaced_count += 1

    print(f"Replaced {replaced_count} textures.")
    with open(out_bundle, "wb") as f:
        f.write(env.file.save(packer="lz4"))
    
    print(f"Saved patched bundle to: {out_bundle} (Size: {os.path.getsize(out_bundle)} bytes)")

if __name__ == "__main__":
    opt = sys.argv[1] if len(sys.argv) > 1 else "A"
    patch_bee(opt)
