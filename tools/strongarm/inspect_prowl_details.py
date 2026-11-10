import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

prowl_bundle = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
print(f"Loading {prowl_bundle}...")
env = UnityPy.load(str(prowl_bundle))

print("Objects summary:")
types = {}
for obj in env.objects:
    t = obj.type.name
    types[t] = types.get(t, 0) + 1
for t, count in sorted(types.items()):
    print(f"  {t}: {count}")

print("\nAssetBundle m_Container:")
for obj in env.objects:
    if obj.type.name == "AssetBundle":
        tree = obj.read_typetree()
        for k, v in tree.get("m_Container", []):
            print(f"  {k} -> {v.get('asset', {}).get('m_PathID')}")

print("\nMeshes:")
for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        print(f"  Mesh: {tree.get('m_Name')} (verts={tree.get('m_VertexData', {}).get('m_VertexCount')})")

print("\nMaterials:")
for obj in env.objects:
    if obj.type.name == "Material":
        tree = obj.read_typetree()
        print(f"  Mat: {tree.get('m_Name')} (PID={obj.path_id})")

print("\nTextures:")
for obj in env.objects:
    if obj.type.name == "Texture2D":
        tree = obj.read_typetree()
        print(f"  Tex: {tree.get('m_Name')} (PID={obj.path_id})")

print("\nSkinnedMeshRenderers:")
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        mesh_pid = tree.get("m_Mesh", {}).get("m_PathID")
        bones_count = len(tree.get("m_Bones", []))
        print(f"  SMR: PID={obj.path_id}, Mesh PID={mesh_pid}, Bones={bones_count}")
