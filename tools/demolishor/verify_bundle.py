# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path(r"d:\Agent\tftf\toolchain\unity_build_project\AssetBundles\demolishor_mesh.assetbundle")
print(f"Loading {bundle_path.name} ({bundle_path.stat().st_size} bytes)...")

env = UnityPy.load(str(bundle_path))
print(f"Total objects in bundle: {len(env.objects)}")

types = {}
for obj in env.objects:
    t = obj.type.name
    types[t] = types.get(t, 0) + 1

print("\nObjects by type:")
for t, c in sorted(types.items(), key=lambda x: x[1], reverse=True):
    print(f"  {t}: {c}")

print("\n--- Meshes in Bundle ---")
for obj in env.objects:
    if obj.type.name == "Mesh":
        mesh = obj.read()
        print(f"  Mesh: {mesh.m_Name}")
        tree = obj.read_typetree()
        v_count = tree.get("m_VertexData", {}).get("m_VertexCount", 0)
        submeshes = len(tree.get("m_SubMeshes", []))
        bindposes = len(tree.get("m_BindPose", []))
        print(f"    Vertex count: {v_count}, submeshes: {submeshes}, bindposes: {bindposes}")

print("\n--- Textures in Bundle ---")
for obj in env.objects:
    if obj.type.name == "Texture2D":
        t = obj.read()
        print(f"  Texture: {t.m_Name} ({t.m_Width}x{t.m_Height}, format: {t.m_TextureFormat})")

print("\n--- Materials in Bundle ---")
for obj in env.objects:
    if obj.type.name == "Material":
        mat = obj.read()
        print(f"  Material: {mat.m_Name}")

print("\n--- GameObjects / Models in Bundle ---")
for obj in env.objects:
    if obj.type.name == "GameObject":
        go = obj.read()
        print(f"  GameObject: {go.m_Name}")
