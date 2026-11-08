import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
from collections import Counter
import json

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")
env = UnityPy.load(str(bundle_path))

with open(r"E:\Agent\TFTF-blender\tools\vortex\grindor_45_vh_bones.json", "r", encoding="utf-8") as f:
    bones = json.load(f)

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_grindor_cin_rotf_01":
            print("Found cha_grindor_cin_rotf_01!")
            skin = tree.get("m_Skin", [])
            print(f"Skin entries: {len(skin)}")
            counts = Counter()
            for s in skin:
                # s has weight and boneIndex
                for bi in [s.get(f"m_BoneIndex_{i}") for i in range(4)]:
                    if bi is not None and bi < len(bones):
                        counts[bones[bi]] += 1
            print("Grindor vehicle bone weight usage:")
            for bname, cnt in counts.most_common():
                print(f"  {bname:25s}: {cnt} verts")
