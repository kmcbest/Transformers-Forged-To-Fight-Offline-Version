import sys
from pathlib import Path
import UnityPy

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

env_b = UnityPy.load("assets_redeco/brawl_gs.assetbundle")
env_t = UnityPy.load("assets_redeco/tarn_gs.assetbundle")

sf_b = list(env_b.files.values())[0] if not hasattr(list(env_b.files.values())[0], 'files') else list(list(env_b.files.values())[0].files.values())[0]
sf_t = list(env_t.files.values())[0] if not hasattr(list(env_t.files.values())[0], 'files') else list(list(env_t.files.values())[0].files.values())[0]

mesh_b = sf_b.objects[8927022796776742380].read_typetree()
mesh_t = next(o for o in sf_t.objects.values() if o.type.name == "Mesh" and "cha_tarn_gs_00" in o.read_typetree().get("m_Name", "")).read_typetree()

print("--- Mesh Comparison ---")
print("Brawl Mesh Name:", mesh_b.get("m_Name"))
print("Tarn Mesh Name:", mesh_t.get("m_Name"))

print("Brawl SubMeshes count:", len(mesh_b.get("m_SubMeshes", [])))
print("Tarn SubMeshes count:", len(mesh_t.get("m_SubMeshes", [])))
print("Brawl SubMesh 0:", mesh_b.get("m_SubMeshes", [])[0])
print("Tarn SubMesh 0:", mesh_t.get("m_SubMeshes", [])[0])

print("Brawl BoneNameHashes count:", len(mesh_b.get("m_BoneNameHashes", [])))
print("Tarn BoneNameHashes count:", len(mesh_t.get("m_BoneNameHashes", [])))

print("Brawl BindPose count:", len(mesh_b.get("m_BindPose", [])))
print("Tarn BindPose count:", len(mesh_t.get("m_BindPose", [])))

print("Brawl VertexData channels:")
for c in mesh_b.get("m_VertexData", {}).get("m_Channels", []):
    if c.get("dimension") > 0:
        print("  Brawl channel:", c)

print("Tarn VertexData channels:")
for c in mesh_t.get("m_VertexData", {}).get("m_Channels", []):
    if c.get("dimension") > 0:
        print("  Tarn channel:", c)
