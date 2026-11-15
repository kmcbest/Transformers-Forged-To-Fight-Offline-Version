import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import json
import UnityPy

MOVES_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")
print(f"Loading {MOVES_BUNDLE}...")
env = UnityPy.load(str(MOVES_BUNDLE))

target_pid = -8528702938335562906
obj_map = {o.path_id: o for o in env.objects}

if target_pid not in obj_map:
    print(f"Error: target PID {target_pid} not found in moves.assetbundle!")
    sys.exit(1)

o = obj_map[target_pid]
tt = o.read_typetree()
script = tt.get("m_Script", "")
if isinstance(script, bytes):
    script = script.decode("utf-8", errors="ignore")

data = json.loads(script)
events = data["moves"]["events"]

# Filter out old SlideMoveEvent
events = [ev for ev in events if ev.get("type") != "SlideMoveEvent"]

# Insert new SlideMoveEvent:
# Full-screen dash/ram: tt=False (not capped by melee range!), sd=26.0m, d=16 frames (f=2 to 18)
slide_event = {
    "type": "SlideMoveEvent",
    "sc": [],
    "sd": 26.0,
    "inf": False,
    "tar": 0,
    "mn": "move_heavy_ramjet_donut",
    "tt": False,
    "ccs": True,
    "cc": [],
    "dn": "SlideMoveEvent--jet_charge",
    "di": 0.0,
    "id": -9998881,
    "d": 16,
    "f": 2,
    "om": False,
}
events.insert(0, slide_event)
events.sort(key=lambda x: x.get("f", 0))
data["moves"]["events"] = events
new_script = json.dumps(data, indent=4)
tt["m_Script"] = new_script
o.save_typetree(tt)
print(f"[+] Configured SlideMoveEvent (tt=False, sd=26.0, di=0.0, f=2, d=16) in move_heavy_ramjet_donut!")

# Save bundle with packer="lz4"
output_bytes = env.file.save(packer="lz4")
MOVES_BUNDLE.write_bytes(output_bytes)
print(f"[+] Saved {MOVES_BUNDLE} ({len(output_bytes)/(1024*1024):.2f} MB, packer='lz4')")

# Verification
verify_env = UnityPy.load(str(MOVES_BUNDLE))
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

# Verify slide event inside reloaded move
v_obj = {obj.path_id: obj for obj in verify_env.objects}[target_pid]
v_data = json.loads(v_obj.read_typetree()["m_Script"])
slide_evs = [ev for ev in v_data["moves"]["events"] if ev.get("type") == "SlideMoveEvent"]
print(f"[*] Verified SlideMoveEvents in reloaded move: {slide_evs}")
print("[✓] ALL QUALITY GATES PASSED!")
