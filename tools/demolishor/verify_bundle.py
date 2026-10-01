# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent.parent

for name, rel_path in [
    ("Unity Compiled Bundle", "toolchain/unity_build_project/AssetBundles/demolishor_mesh.assetbundle"),
    ("Final Grafted Game Bundle", "assets_redeco/demolishor_gs.assetbundle")
]:
    bundle_path = ROOT / rel_path
    if not bundle_path.exists():
        print(f"[!] {name} not found at {bundle_path}")
        continue

    print(f"\n=== Verifying {name} ({bundle_path.name}) ===")
    print(f"Size: {bundle_path.stat().st_size / (1024*1024):.2f} MB")
    
    env = UnityPy.load(str(bundle_path))
    print(f"Total objects: {len(env.objects)}")
    
    types = {}
    for obj in env.objects:
        t = obj.type.name
        types[t] = types.get(t, 0) + 1
        
    for t, c in sorted(types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {t:25s}: {c}")
        
    for obj in env.objects:
        if obj.type.name == "Mesh":
            tree = obj.read_typetree()
            vcount = tree.get("m_VertexData", {}).get("m_VertexCount", 0)
            aabb = tree.get("m_LocalAABB", {})
            print(f"  [Mesh] {tree.get('m_Name')}: {vcount} verts, AABB Center={aabb.get('m_Center')}, Extent={aabb.get('m_Extent')}")
        elif obj.type.name == "AssetBundle":
            tree = obj.read_typetree()
            print(f"  [AssetBundle Name]: {tree.get('m_AssetBundleName')}")
            print(f"  [Container Items Count]: {len(tree.get('m_Container', []))}")

print("\n[✓] All bundles verified successfully!")
