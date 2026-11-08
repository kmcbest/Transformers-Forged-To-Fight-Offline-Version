import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import io
import UnityPy
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen

ROOT = Path(__file__).resolve().parent.parent

# 1. Load source font with E99F (Mercenary icon)
tec_path = ROOT / "Tecnica_Bold_with_E99F.ttf"
if not tec_path.exists():
    print(f"ERROR: {tec_path} not found!")
    sys.exit(1)

tt_tec = TTFont(str(tec_path))
glyph_set = tt_tec.getGlyphSet()
g_e99f = glyph_set['uniE99F']
width, lsb = tt_tec['hmtx']['uniE99F']
print(f"[+] Extracted uniE99F: width={width}, lsb={lsb}")

# 2. Base clean from extracted_apk
bundle_path = ROOT / "extracted_apk/assets/assetpack/chinesesimplified_odr/chinesesimplified.assetbundle"
if not bundle_path.exists():
    bundle_path = ROOT / "assets_redeco/chinesesimplified.assetbundle"

print(f"[+] Loading {bundle_path}...")
env = UnityPy.load(str(bundle_path))

patched_count = 0
for obj in env.objects:
    if obj.type.name == "Font":
        data = obj.read()
        font_name = data.m_Name
        print(f"[*] Checking font: {font_name}...")
        
        font_bytes = bytes(data.m_FontData)
        tt = TTFont(io.BytesIO(font_bytes))
        
        print(f"[*] Patching 0xE99F into {font_name}...")
        
        # 1. GlyphOrder
        order = list(tt.getGlyphOrder())
        if 'uniE99F' not in order:
            order.append('uniE99F')
            tt.setGlyphOrder(order)
        
        # 2. hmtx
        tt['hmtx']['uniE99F'] = (width, lsb)
        
        # 3. CFF
        if 'CFF ' in tt:
            cff = tt['CFF '].cff
            top_dict = cff.topDictIndex[0]
            cs = top_dict.CharStrings
            
            pen = T2CharStringPen(width, glyph_set)
            g_e99f.draw(pen)
            t2_cs = pen.getCharString()
            t2_cs.private = top_dict.Private
            
            if 'uniE99F' not in top_dict.charset:
                top_dict.charset.append('uniE99F')
            idx = len(cs.charStringsIndex)
            cs.charStringsIndex.append(t2_cs)
            cs.charStrings['uniE99F'] = idx
            
        # 4. cmap (format 4 and format 12 tables)
        for table in tt['cmap'].tables:
            if table.format in (4, 12):
                table.cmap[0xE99F] = 'uniE99F'
                
        # Save font to bytes
        buf = io.BytesIO()
        tt.save(buf)
        patched_data = buf.getvalue()
        
        # Verify
        verify_tt = TTFont(io.BytesIO(patched_data))
        cmap = verify_tt.getBestCmap()
        assert 0xE99F in cmap, f"Failed to add 0xE99F to {font_name} cmap!"
        
        fmt4_ok = any(t.format == 4 and 0xE99F in t.cmap for t in verify_tt['cmap'].tables)
        fmt12_ok = any(t.format == 12 and 0xE99F in t.cmap for t in verify_tt['cmap'].tables)
        print(f"  [OK] Injected uniE99F into {font_name}! fmt4={fmt4_ok}, fmt12={fmt12_ok}, Size: {len(patched_data)} bytes")
        assert fmt4_ok, f"Format 4 missing 0xE99F in {font_name}!"
        
        data.m_FontData = patched_data
        data.save()
        patched_count += 1

assert patched_count > 0, "No fonts were patched!"

# 3. Save modified AssetBundle
out_bundle_path = ROOT / "assets_redeco/chinesesimplified.assetbundle"
print(f"[+] Saving to {out_bundle_path} with LZ4 compression...")
with open(out_bundle_path, "wb") as f:
    f.write(env.file.save(packer="lz4"))

print(f"[+] Successfully saved {out_bundle_path} ({out_bundle_path.stat().st_size} bytes)")

# 4. Final verification
check_env = UnityPy.load(str(out_bundle_path))
for obj in check_env.objects:
    if obj.type.name == "Font":
        f_data = obj.read()
        f_tt = TTFont(io.BytesIO(bytes(f_data.m_FontData)))
        c = f_tt.getBestCmap()
        print(f"[VERIFY] {f_data.m_Name}: 0xE99F in cmap: {0xE99F in c} ({c.get(0xE99F)})")
