import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(bundle_path))

print(f"=== Probing Ramjet PIDs ===")
meshes = []
materials = []
textures = []
smrs = []

for obj in env.objects:
    tname = obj.type.name
    try:
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        if tname == "Mesh":
            meshes.append((name, obj.path_id))
        elif tname == "Material":
            materials.append((name, obj.path_id))
        elif tname == "Texture2D":
            textures.append((name, obj.path_id))
        elif tname == "SkinnedMeshRenderer":
            mesh_ref = tt.get("m_Mesh", {}).get("m_PathID")
            smrs.append((obj.path_id, mesh_ref))
    except:
        pass

print("\n--- Meshes ---")
for n, pid in meshes:
    print(f"  {n}: PID = {pid}")

print("\n--- Materials ---")
for n, pid in materials:
    print(f"  {n}: PID = {pid}")

print("\n--- Textures ---")
for n, pid in textures:
    print(f"  {n}: PID = {pid}")

print("\n--- SkinnedMeshRenderers ---")
for pid, mref in smrs:
    print(f"  SMR PID = {pid}, Mesh PID = {mref}")
