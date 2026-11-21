import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

asset_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Swoop\Ramjet\cha_ramjet_official_00.asset")
env = UnityPy.load(str(asset_path))

for obj in env.objects:
    if obj.type.name == "Mesh":
        mesh = obj.read()
        print("Mesh name:", getattr(mesh, "m_Name", ""))
        print("Bindposes count:", len(mesh.m_BindPose))
        # inspect skin bone indices
        skin = getattr(mesh, "m_Skin", [])
        if skin:
            print("Found skin bone weights:", len(skin))
            # print max bone index
            max_bi = max(max(sw.m_BoneIndex) for sw in skin)
            print("Max bone index:", max_bi)
            # count weights per bone index
            bi_counts = {}
            for sw in skin:
                for bi, w in zip(sw.m_BoneIndex, sw.m_Weight):
                    if w > 0.4:
                        bi_counts[bi] = bi_counts.get(bi, 0) + 1
            for bi, cnt in sorted(bi_counts.items(), key=lambda x: -x[1]):
                print(f"  Bone index {bi}: {cnt} verts")
