import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bp = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
env = UnityPy.load(str(bp))

# Find avatars
avatars = {}
for obj in env.objects:
    if obj.type.name == "Avatar":
        d = obj.read()
        name = getattr(d, 'name', getattr(d, 'm_Name', ''))
        avatars[name] = obj.path_id
        avatars[f"assets/avatars/{name.lower()}.asset"] = obj.path_id
        avatars[f"assets/avatars/{name}.asset"] = obj.path_id
        print(f"  Registering Avatar: '{name}' -> PathID {obj.path_id}")

# Add to AssetBundle m_Container
for obj in env.objects:
    if obj.type.name == "AssetBundle":
        tree = obj.read_typetree()
        c = tree.get("m_Container", [])
        existing_keys = {item[0] for item in c}
        for name, pid in avatars.items():
            if name not in existing_keys:
                entry = (name, {'preloadIndex': 0, 'preloadSize': 0, 'asset': {'m_FileID': 0, 'm_PathID': pid}})
                c.append(entry)
                print(f"  Added '{name}' to m_Container")
        tree["m_Container"] = c
        obj.save_typetree(tree)

with open(bp, "wb") as f:
    f.write(env.file.save(packer="lz4"))

print(f"[✓] Successfully registered all Avatars into {bp}!")
