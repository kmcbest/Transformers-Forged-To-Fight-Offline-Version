import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import zlib

p_bundle = Path(r"E:\Agent\TFTF-blender\toolchain\grindor_anims_registered.assetbundle")
if not p_bundle.exists():
    p_bundle = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")

env = UnityPy.load(str(p_bundle))

go_dict = {}
tr_dict = {}
tr_to_go = {}
for obj in env.objects:
    if obj.type.name == "GameObject":
        go_dict[obj.path_id] = obj.read_typetree()
    elif obj.type.name == "Transform":
        tr = obj.read_typetree()
        tr_dict[obj.path_id] = tr
        go_id = tr.get("m_GameObject", {}).get("m_PathID")
        tr_to_go[obj.path_id] = go_id

clip_hashes = set()
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "frontend_Grindor_levelup_vehicle_idle_transformed":
            for b in tree.get("m_ClipBindingConstant", {}).get("genericBindings", []):
                clip_hashes.add(b.get("path"))

# Build path from root for every transform in Prefab 1
P1_ROOT_ID = 4940518313520681104
def build_paths(root_go_id):
    paths = {}
    def recurse(go_id, current_path):
        go = go_dict.get(go_id)
        if not go: return
        name = go.get("m_Name")
        new_path = f"{current_path}/{name}" if current_path else name
        paths[go_id] = new_path
        # find transform
        for tr_id, tr in tr_dict.items():
            if tr_to_go.get(tr_id) == go_id:
                for child in tr.get("m_Children", []):
                    c_tr_id = child.get("m_PathID")
                    c_go_id = tr_to_go.get(c_tr_id)
                    recurse(c_go_id, new_path)
    recurse(root_go_id, "")
    return paths

paths = build_paths(P1_ROOT_ID)
print(f"Total gameobjects under P1: {len(paths)}")
matched = 0
for go_id, full_path in paths.items():
    # Relative path from Animator (which is at P1_ROOT)
    parts = full_path.split("/")
    rel_path = "/".join(parts[1:])
    h = zlib.crc32(rel_path.encode('utf-8'))
    if h in clip_hashes:
        matched += 1
        print(f"[MATCH {matched:2d}] {parts[-1]:25s} -> {rel_path}")

print(f"\nTotal matched: {matched} / {len(clip_hashes)}")
