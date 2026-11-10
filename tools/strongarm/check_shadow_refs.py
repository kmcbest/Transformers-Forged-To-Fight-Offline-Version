import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from UnityPy.enums import TextureFormat
from pathlib import Path

for code in (3, 4, 7, 34, 45, 47):
    print(f"TextureFormat({code}) = {TextureFormat(code)}")

p = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
env = UnityPy.load(str(p))

shadow_pids = {-1097663200202977369, -54785902815187665}
def find_refs(obj_id, tree, path=""):
    if isinstance(tree, dict):
        if tree.get("m_PathID") in shadow_pids:
            print(f"REF to {tree.get('m_PathID')} in {obj_id} at {path}")
        for k, v in tree.items():
            find_refs(obj_id, v, f"{path}.{k}")
    elif isinstance(tree, list):
        for i, v in enumerate(tree):
            find_refs(obj_id, v, f"{path}[{i}]")

for obj in env.objects:
    if obj.type.name != "Texture2D":
        try:
            tree = obj.read_typetree()
            find_refs(f"{obj.type.name}({obj.path_id})", tree)
        except Exception:
            pass
