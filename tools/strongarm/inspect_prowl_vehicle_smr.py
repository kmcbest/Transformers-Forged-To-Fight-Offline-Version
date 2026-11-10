import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p_prowl = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
env = UnityPy.load(str(p_prowl))

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        go_name = tree.get("m_GameObject", {}).get("m_PathID", 0)
        bones = tree.get("m_Bones", [])
        if len(bones) == 26:
            print("Found Vehicle SMR (26 bones):")
            print("  m_AABB:", tree.get("m_AABB"))
            mesh_ptr = tree.get("m_Mesh", {})
            print("  m_Mesh:", mesh_ptr)
            # Find bone names
            # Find transform nodes in bundle
    elif obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if "01" in tree.get("m_Name", ""):
            print(f"Vehicle Mesh: {tree.get('m_Name')}")
            print(f"  m_LocalAABB: {tree.get('m_LocalAABB')}")
            hashes = tree.get("m_BoneNameHashes", [])
            print(f"  m_BoneNameHashes ({len(hashes)}): {hashes}")

# Also find bone names from Prefab
for obj in env.objects:
    if obj.type.name == "GameObject":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "Prowl_GS_Deluxe2016":
            print("\nFound Prefab: Prowl_GS_Deluxe2016")
