import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

root = Path(r"E:\Agent\TFTF-blender")
bp = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")
out_bp = root / "toolchain" / "grindor_anims_registered.assetbundle"

env = UnityPy.load(str(bp))

anim_entries = {}
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        d = obj.read()
        name = getattr(d, 'name', None) or getattr(d, 'm_Name', '')
        anim_entries[f"assets/anims/{name.lower()}.anim"] = obj.path_id
        anim_entries[f"assets/anims/{name}.anim"] = obj.path_id

print(f"Found {len(anim_entries)//2} animation clips to register.")

for obj in env.objects:
    if obj.type.name == "AssetBundle":
        tree = obj.read_typetree()
        c = tree.get("m_Container", [])
        for name, pid in anim_entries.items():
            entry = (name, {'preloadIndex': 0, 'preloadSize': 0, 'asset': {'m_FileID': 0, 'm_PathID': pid}})
            c.append(entry)
        tree["m_Container"] = c
        obj.save_typetree(tree)
        print("Updated AssetBundle container with animation clips!")

with open(out_bp, "wb") as f:
    f.write(env.file.save(packer="lz4"))

print(f"[✓] Saved bundle with registered clips to: {out_bp} ({out_bp.stat().st_size / 1024 / 1024:.2f} MB)")
