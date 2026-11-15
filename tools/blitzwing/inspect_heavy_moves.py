import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

env = UnityPy.load(r"E:\Agent\TFTF-blender\assets_netflix\moves.assetbundle")

moves = []
for obj in env.objects:
    if obj.type.name == "TextAsset":
        data = obj.read()
        name = getattr(data, "m_Name", "")
        moves.append(name)

print(f"Total TextAsset moves: {len(moves)}")

print("\n--- Heavy Moves ---")
for m in sorted(moves):
    if "heavy" in m.lower():
        print(f"  {m}")

print("\n--- Megatron Moves ---")
for m in sorted(moves):
    if "megat" in m.lower():
        print(f"  {m}")

print("\n--- Ramjet / Jet / Seeker Heavy Moves ---")
for m in sorted(moves):
    if any(k in m.lower() for k in ("ramjet", "seeker", "jet", "starscream")):
        if any(k in m.lower() for k in ("heavy", "special", "ram")):
            print(f"  {m}")
