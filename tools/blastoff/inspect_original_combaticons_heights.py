import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
from mathutils import Vector

fbx_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\transformers fall of cybertron convaticons .fbx")
print(f"Loading {fbx_path}...")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

bots = ["BlastOff", "Brawl", "Onslaught", "Vortex", "Swindle", "Bruticus"]
groups = {b: {"robot": [], "vehicle": [], "other": []} for b in bots}

for obj in bpy.data.objects:
    if obj.type == "MESH":
        name = obj.name
        low = name.lower()
        matched_bot = None
        for b in bots:
            if b.lower() in low or (b == "Onslaught" and "onslaght" in low):
                matched_bot = b
                break
        if not matched_bot:
            continue
        
        mode = "other"
        if name.startswith("RB_") or "charskel" in low or "robot" in low:
            mode = "robot"
        elif name.startswith("VH_") or "vehicle" in low:
            mode = "vehicle"
        elif "wing" in low or "prop" in low or "rotor" in low:
            mode = "robot"
            
        bbox = [obj.matrix_world @ Vector(b) for b in obj.bound_box]
        min_z = min(b.z for b in bbox)
        max_z = max(b.z for b in bbox)
        min_y = min(b.y for b in bbox)
        max_y = max(b.y for b in bbox)
        min_x = min(b.x for b in bbox)
        max_x = max(b.x for b in bbox)
        h = max_z - min_z
        groups[matched_bot][mode].append((obj.name, min_x, max_x, min_y, max_y, min_z, max_z, h))

print("\n=== Combaticons Robot Heights in Original Scene ===")
for b in bots:
    rob_objs = groups[b]["robot"]
    if rob_objs:
        all_min_z = min(o[5] for o in rob_objs)
        all_max_z = max(o[6] for o in rob_objs)
        all_min_x = min(o[1] for o in rob_objs)
        all_max_x = max(o[2] for o in rob_objs)
        all_min_y = min(o[3] for o in rob_objs)
        all_max_y = max(o[4] for o in rob_objs)
        h = all_max_z - all_min_z
        print(f"Bot: {b:10s} (Robot Mode) | Objs: {len(rob_objs):2d} | Height: {h:6.3f}m | Z=[{all_min_z:+.2f}, {all_max_z:+.2f}] | Y=[{all_min_y:+.2f}, {all_max_y:+.2f}] | X=[{all_min_x:+.2f}, {all_max_x:+.2f}]")

print("\n=== Detailed List of Objects per Bot ===")
for b in bots:
    print(f"\n--- {b} ---")
    for mode in ["robot", "vehicle", "other"]:
        for name, x0, x1, y0, y1, z0, z1, h in groups[b][mode]:
            print(f"  [{mode:7s}] {name:35s} | H={h:6.3f} | Z=[{z0:+.2f}, {z1:+.2f}]")
