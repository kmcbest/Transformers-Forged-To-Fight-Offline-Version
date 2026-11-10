import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
from pathlib import Path
import UnityPy

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
print(f"Reading bundle: {bundle_path} (exists={bundle_path.exists()}, size={bundle_path.stat().st_size if bundle_path.exists() else 0} bytes)")

env = UnityPy.load(str(bundle_path))

gos = []
smrs = []
meshes = []
mats = []
texs = []
clips = []

for obj in env.objects:
    try:
        if obj.type.name == "GameObject":
            data = obj.read()
            gos.append(data.m_Name)
        elif obj.type.name == "SkinnedMeshRenderer":
            data = obj.read()
            go_name = data.m_GameObject.read().m_Name if data.m_GameObject else "None"
            mesh_name = data.m_Mesh.read().m_Name if data.m_Mesh else "None"
            bones_cnt = len(data.m_Bones)
            smrs.append((go_name, mesh_name, bones_cnt))
        elif obj.type.name == "Mesh":
            data = obj.read()
            v_cnt = len(data.m_Vertices) if data.m_Vertices else 0
            b_cnt = len(data.m_BoneNameHashes) if hasattr(data, 'm_BoneNameHashes') and data.m_BoneNameHashes else 0
            meshes.append((data.m_Name, v_cnt, b_cnt))
        elif obj.type.name == "Material":
            data = obj.read()
            mats.append(data.m_Name)
        elif obj.type.name == "Texture2D":
            data = obj.read()
            texs.append((data.m_Name, data.m_Width, data.m_Height))
        elif obj.type.name == "AnimationClip":
            data = obj.read()
            clips.append(data.m_Name)
    except Exception as e:
        print(f"Error reading {obj.type.name}: {e}")

print(f"\n--- GameObjects ({len(gos)}) ---")
for g in gos[:25]:
    print("  ", g)
if len(gos) > 25:
    print(f"  ... and {len(gos)-25} more")

print(f"\n--- SkinnedMeshRenderers ({len(smrs)}) ---")
for s in smrs:
    print(f"  GO: {s[0]}, Mesh: {s[1]}, Bones: {s[2]}")

print(f"\n--- Meshes ({len(meshes)}) ---")
for m in meshes:
    print(f"  Mesh: {m[0]}, Verts: {m[1]}, BonesHashes: {m[2]}")

print(f"\n--- Textures ({len(texs)}) ---")
for t in texs:
    print(f"  Texture: {t[0]} ({t[1]}x{t[2]})")

print(f"\n--- Materials ({len(mats)}) ---")
for m in mats:
    print(f"  Material: {m}")

print(f"\n--- AnimationClips ({len(clips)}) ---")
for c in clips:
    print(f"  Clip: {c}")
