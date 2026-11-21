import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

moves_path = r"E:\Agent\TFTF\assets_netflix\moves.assetbundle"
env = UnityPy.load(moves_path)

print(f"Total objects in moves.assetbundle: {len(env.objects)}")
matches = []
for obj in env.objects:
    try:
        tree = obj.read_typetree()
        name = tree.get("m_Name", "")
        if "handgun" in name.lower() or "left" in name.lower() or "motormaster" in name.lower():
            matches.append((obj.path_id, obj.type.name, name))
    except:
        pass

print(f"Matches ({len(matches)}):")
for pid, tname, mname in matches[:40]:
    print(f"  {pid} ({tname}): {mname}")
