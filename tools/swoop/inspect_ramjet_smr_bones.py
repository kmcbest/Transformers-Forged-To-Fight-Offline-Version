import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        smr = obj.read()
        go_name = smr.m_GameObject.read().m_Name
        if go_name == "cha_ramjet_gs_deluxe2008_00":
            bones = [b.read().m_GameObject.read().m_Name for b in smr.m_Bones]
            mesh = smr.m_Mesh.read()
            skin = mesh.m_Skin
            bone_vert_count = {b: 0 for b in bones}
            for sw in skin:
                for b_idx, w in zip(sw.m_BoneIndex, sw.m_Weight):
                    if w > 0.4:
                        bone_vert_count[bones[b_idx]] += 1
            for b, c in sorted(bone_vert_count.items(), key=lambda x: -x[1]):
                if "shoulder" in b.lower() or "arm" in b.lower() or "spine" in b.lower():
                    print(f"  {b}: {c} verts")
            break
