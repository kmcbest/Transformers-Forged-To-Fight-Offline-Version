import sys
import UnityPy
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent

# 1. Prepare patched TTF bytes
patched_ttf_path = ROOT / "tools" / "NotoSansSC-Light-Patched.ttf"
if not patched_ttf_path.exists():
    print("Generating patched TTF...")
    tt_tec = TTFont(str(ROOT / "tools/web_dashboard/Tecnica_Bold_116.ttf"))
    tt_noto = TTFont(str(ROOT / "tools/NotoSansSC-Light.ttf"))
    glyf_tec = tt_tec["glyf"]
    g_e517 = glyf_tec["uniE517"]
    width_tec = tt_tec["hmtx"]["uniE517"][0]

    cff = tt_noto["CFF "]
    top_dict = cff.cff.topDictIndex[0]
    charstrings = top_dict.CharStrings
    orig_armor_up = charstrings["armor_up"]

    pen = T2CharStringPen(width_tec, None)
    g_e517.draw(pen, glyf_tec)
    cs_e517 = pen.getCharString()
    cs_e517.private = orig_armor_up.private

    charstrings["armor_up"] = cs_e517
    tt_noto["hmtx"]["armor_up"] = tt_tec["hmtx"]["uniE517"]
    tt_noto.save(str(patched_ttf_path))
    print("Patched TTF saved.")

patched_font_bytes = patched_ttf_path.read_bytes()
print(f"Patched font size: {len(patched_font_bytes)} bytes")

# 2. Load original chinesesimplified.assetbundle
orig_bundle_path = ROOT / "extracted_apk/assets/assetpack/chinesesimplified_odr/chinesesimplified.assetbundle"
print(f"Loading {orig_bundle_path}...")
env = UnityPy.load(str(orig_bundle_path))

found = False
for obj in env.objects:
    if obj.type.name == "Font":
        font_data = obj.read()
        if font_data.m_Name == "NotoSansSC-Light":
            print("Found NotoSansSC-Light, replacing font data...")
            font_data.m_FontData = patched_font_bytes
            font_data.save()
            found = True
            break

if not found:
    print("ERROR: NotoSansSC-Light not found in bundle!")
    sys.exit(1)

# 3. Save modified AssetBundle with LZ4 compression
out_bundle_path = ROOT / "assets_redeco/chinesesimplified.assetbundle"
out_bundle_path.parent.mkdir(parents=True, exist_ok=True)
print(f"Saving modified AssetBundle to {out_bundle_path} with LZ4 compression...")
with open(out_bundle_path, "wb") as f:
    f.write(env.file.save(packer="lz4"))

print(f"Saved {out_bundle_path} ({out_bundle_path.stat().st_size} bytes)")

# 4. Verify by reloading
print("Verifying saved bundle...")
verify_env = UnityPy.load(str(out_bundle_path))
verified = False
for obj in verify_env.objects:
    if obj.type.name == "Font":
        v_font = obj.read()
        if v_font.m_Name == "NotoSansSC-Light":
            v_bytes = bytes(v_font.m_FontData)
            print(f"Verified font data length: {len(v_bytes)} (expected {len(patched_font_bytes)})")
            assert len(v_bytes) == len(patched_font_bytes), "Length mismatch!"
            verified = True
            break

assert verified, "Verification failed to find font!"
print("SUCCESS: chinesesimplified.assetbundle patched and verified successfully!")
