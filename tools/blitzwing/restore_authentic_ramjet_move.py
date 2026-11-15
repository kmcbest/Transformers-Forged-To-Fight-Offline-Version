import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import json
import UnityPy

NETFLIX_MOVES = Path(r"E:\Agent\TFTF-blender\assets_netflix\moves.assetbundle")
REDECO_MOVES = Path(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")

print(f"Loading authentic move from {NETFLIX_MOVES}...")
env_src = UnityPy.load(str(NETFLIX_MOVES))
authentic_script = None
for o in env_src.objects:
    if o.type.name == "TextAsset":
        d = o.read()
        if getattr(d, "m_Name", "") == "move_heavy_ramjet_donut":
            raw = getattr(d, "m_Script", b"")
            authentic_script = raw.decode('utf-8', errors='replace') if isinstance(raw, (bytes, bytearray)) else str(raw)
            break

assert authentic_script is not None, "Failed to find move_heavy_ramjet_donut in Netflix moves!"
auth_data = json.loads(authentic_script)
print(f"[+] Found authentic move_heavy_ramjet_donut with {len(auth_data['moves']['events'])} events (NO SlideMoveEvent)")

print(f"\nPatching into {REDECO_MOVES}...")
env_dst = UnityPy.load(str(REDECO_MOVES))
patched = False
for o in env_dst.objects:
    if o.type.name == "TextAsset":
        d = o.read()
        if getattr(d, "m_Name", "") == "move_heavy_ramjet_donut":
            tt = o.read_typetree()
            tt["m_Script"] = authentic_script
            o.save_typetree(tt)
            patched = True
            break

assert patched, "Failed to patch move_heavy_ramjet_donut in redeco moves!"

output_bytes = env_dst.file.save(packer="lz4")
REDECO_MOVES.write_bytes(output_bytes)
print(f"[✓] Saved {REDECO_MOVES} ({len(output_bytes)/(1024*1024):.2f} MB, packer='lz4')")

# Verification
verify_env = UnityPy.load(str(REDECO_MOVES))
moves = [obj for obj in verify_env.objects if obj.type.name == "TextAsset"]
names = set()
for obj in moves:
    try:
        names.add(obj.read_typetree().get("m_Name"))
    except:
        pass

print(f"[*] Verified moves count: {len(moves)} (gate: >= 945)")
assert len(moves) >= 945, f"Move count {len(moves)} < 945!"
assert "move_lifeline_special_01" in names, "Missing move_lifeline_special_01!"
assert "move_lifeline_special_02" in names, "Missing move_lifeline_special_02!"
assert "move_heavy_ramjet_donut" in names, "Missing move_heavy_ramjet_donut!"

for o in verify_env.objects:
    if o.type.name == "TextAsset":
        d = o.read()
        if getattr(d, "m_Name", "") == "move_heavy_ramjet_donut":
            v_data = json.loads(d.m_Script)
            print(f"[*] Reloaded move_heavy_ramjet_donut has {len(v_data['moves']['events'])} events")
            has_slide = any(ev.get("type") == "SlideMoveEvent" for ev in v_data["moves"]["events"])
            print(f"[*] Has SlideMoveEvent: {has_slide} (should be False)")
            assert not has_slide, "SlideMoveEvent still present!"
print("[✓] Authentic Ramjet Heavy Attack verified!")
