import sys
import os
import zlib
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def u32_crc(s):
    return zlib.crc32(s.encode("utf-8")) & 0xffffffff

print("CRC check:")
for s in ("chop1_back_center", "Reference/COG/chop1_back_center", "COG/chop1_back_center"):
    print(f"  {s:38s} -> {u32_crc(s)}")

b_path = r"E:\Agent\TFTF-blender\assets_redeco\swoop_gs_deluxe2008.assetbundle"
env = UnityPy.load(b_path)
print("\n=== Externals in swoop_gs_deluxe2008.assetbundle ===")
for fname, fobj in env.file.files.items():
    if hasattr(fobj, "externals"):
        for fi, ext in enumerate(fobj.externals, start=1):
            print(f"  [{fname}] fileID={fi}: path={getattr(ext, 'path', ext)}")

for o in env.objects:
    if o.type.name == "AnimatorOverrideController" and o.path_id == 6432204470035570307:
        aoc = o.read_typetree()
        p58 = aoc["m_Clips"][58]
        print(f"\nFight AOC [58]: orig={p58['m_OriginalClip']} over={p58['m_OverrideClip']}")
    if o.type.name == "AssetBundle":
        ab = o.read_typetree()
        pt = ab.get("m_PreloadTable", [])
        in_pt = [p for p in pt if p["m_PathID"] == 7645321843667068633]
        print(f"7645321843667068633 in m_PreloadTable: {in_pt}")

# Check assets_redeco/moves.assetbundle
m_path = r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle"
menv = UnityPy.load(m_path)
print(f"\n=== moves.assetbundle objects count={len(menv.objects)} ===")
types = {}
for o in menv.objects:
    types[o.type.name] = types.get(o.type.name, 0) + 1
print("  types:", types)
for o in menv.objects:
    if o.type.name in ("MonoBehaviour", "TextAsset"):
        try:
            d = o.read()
            nm = getattr(d, "m_Name", "")
            if any(k in nm.lower() for k in ("move_heavy_swoop", "move_heavy_starscream", "move_heavy_ramjet", "move_heavy_skywarp", "move_heavy_grimlock")):
                print(f"\n--- {o.type.name} '{nm}' (pid={o.path_id}) ---")
                if o.type.name == "TextAsset":
                    txt = d.m_Script
                    print(txt[:1500])
                else:
                    tt = o.read_typetree()
                    for k, v in tt.items():
                        if k not in ("m_GameObject", "m_Enabled", "m_Script"):
                            print(f"  {k}: {v}")
        except Exception as e:
            print(f"  err {o.path_id}: {e}")
