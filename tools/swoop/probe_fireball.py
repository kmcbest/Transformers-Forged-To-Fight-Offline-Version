import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import json

MOVES_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")
if not MOVES_BUNDLE.exists():
    MOVES_BUNDLE = Path(r"E:\Agent\TFTF\assets_netflix\moves.assetbundle")

print(f"Loading moves bundle from {MOVES_BUNDLE}...")
env_moves = UnityPy.load(str(MOVES_BUNDLE))

grim_moves = []
for obj in env_moves.objects:
    if obj.type.name in ["TextAsset", "MonoBehaviour"]:
        try:
            d = obj.read_typetree()
            name = d.get("m_Name", "") or ""
            if "grimlock" in name.lower():
                grim_moves.append((obj.type.name, name, obj.path_id))
        except:
            pass

print(f"Found {len(grim_moves)} grimlock objects in moves.assetbundle:")
for t, n, pid in grim_moves:
    if "heavy" in n.lower() or "fire" in n.lower() or "attack" in n.lower() or "special" in n.lower():
        print(f"  [{t}] {n} (PID: {pid})")

# Also check grimlock bundle
GRIM_BUNDLE = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grimlock_gs_mp08_odr\grimlock_gs_mp08.assetbundle")
print(f"\nLoading grimlock bundle from {GRIM_BUNDLE}...")
env_grim = UnityPy.load(str(GRIM_BUNDLE))

fire_objects = []
for obj in env_grim.objects:
    if obj.type.name in ["GameObject", "Prefab", "MonoBehaviour"]:
        try:
            d = obj.read_typetree()
            name = d.get("m_Name", "") or ""
            if any(k in name.lower() for k in ["fire", "heavy", "bullet", "flame", "projectile", "ball"]):
                fire_objects.append((obj.type.name, name, obj.path_id))
        except:
            pass

print(f"Found {len(fire_objects)} fire/projectile objects in grimlock bundle:")
for t, n, pid in fire_objects[:30]:
    print(f"  [{t}] {n} (PID: {pid})")
