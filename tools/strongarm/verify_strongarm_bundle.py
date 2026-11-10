import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p = Path(r"E:\Agent\TFTF-blender\assets_redeco\strongarm_gs.assetbundle")
print(f"Verifying {p} ({p.stat().st_size / (1024*1024):.2f} MB)...")
env = UnityPy.load(str(p))

print("AssetBundle m_Container:")
for obj in env.objects:
    if obj.type.name == "AssetBundle":
        tree = obj.read_typetree()
        for c in tree.get("m_Container", []):
            if "prefab" in c[0] or "avatar" in c[0].lower():
                print(f"  {c[0]} -> PID {c[1].get('asset', {}).get('m_PathID')}")

print("\nMeshes:")
for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        vc = tree.get("m_VertexData", {}).get("m_VertexCount")
        bp = len(tree.get("m_BindPose", []))
        bh = len(tree.get("m_BoneNameHashes", []))
        print(f"  Mesh: '{tree.get('m_Name')}' verts={vc} bindposes={bp} boneHashes={bh}")

print("\nTextures:")
for obj in env.objects:
    if obj.type.name == "Texture2D":
        tree = obj.read_typetree()
        tex = obj.read()
        print(f"  Tex: '{tree.get('m_Name')}' (PID {obj.path_id}) size={tex.image.size if hasattr(tex, 'image') else 'N/A'}")

print("\nSkinnedMeshRenderers:")
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        m_pid = tree.get("m_Mesh", {}).get("m_PathID")
        mats = [m.get("m_PathID") for m in tree.get("m_Materials", [])]
        print(f"  SMR PID {obj.path_id}: Mesh PID={m_pid}, Bones={len(tree.get('m_Bones', []))}, Mats={mats}, Enabled={tree.get('m_Enabled')}")

print("\nAnimatorOverrideController victory:")
for obj in env.objects:
    if obj.type.name == "AnimatorOverrideController":
        tree = obj.read_typetree()
        if "fight" in tree.get("m_Name", "").lower():
            for pair in tree.get("m_Clips", []):
                opid = pair.get("m_OriginalClip", {}).get("m_PathID")
                if opid in (3642901185112467297, -4048722777385356729):
                    print(f"  Override: orig={opid} -> override={pair.get('m_OverrideClip')}")
