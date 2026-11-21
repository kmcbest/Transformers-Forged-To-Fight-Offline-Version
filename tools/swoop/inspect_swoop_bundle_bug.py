import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
TFTF_READ = Path(r"E:\Agent\TFTF")

MESH_BUNDLE = ROOT / "toolchain/unity_build_project/AssetBundles/swoop_mesh.assetbundle"
env_m = UnityPy.load(str(MESH_BUNDLE))
print("=== swoop_mesh.assetbundle Meshes ===")
for o in env_m.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        print(f"  Mesh '{tt['m_Name']}': verts={tt['m_VertexData']['m_VertexCount']}, submeshes={len(tt['m_SubMeshes'])}")
    elif o.type.name == "SkinnedMeshRenderer":
        tt = o.read_typetree()
        print(f"  SMR mats count={len(tt.get('m_Materials', []))}")

SWOOP_BUNDLE = ROOT / "assets_redeco/swoop_gs_deluxe2008.assetbundle"
env_s = UnityPy.load(str(SWOOP_BUNDLE))
obj_map_s = {o.path_id: o for o in env_s.objects}
print("\n=== swoop_gs_deluxe2008.assetbundle Renderers ===")
for o in env_s.objects:
    if o.type.name == "SkinnedMeshRenderer":
        tt = o.read_typetree()
        go_pid = tt["m_GameObject"]["m_PathID"]
        go_name = obj_map_s[go_pid].read_typetree().get("m_Name")
        mats = [m["m_PathID"] for m in tt["m_Materials"]]
        print(f"  SMR PID={o.path_id} GO='{go_name}' en={tt['m_Enabled']} mesh={tt['m_Mesh']['m_PathID']} mats={mats}")

print("\n=== swoop_gs_deluxe2008.assetbundle Textures ===")
for o in env_s.objects:
    if o.type.name == "Texture2D":
        tt = o.read_typetree()
        print(f"  Tex PID={o.path_id}: '{tt['m_Name']}' {tt['m_Width']}x{tt['m_Height']} fmt={tt['m_TextureFormat']} stream={tt['m_StreamData']}")

print("\n=== swoop_gs_deluxe2008.assetbundle Materials ===")
for o in env_s.objects:
    if o.type.name == "Material":
        tt = o.read_typetree()
        texs = {k: v["m_Texture"]["m_PathID"] for k, v in tt["m_SavedProperties"]["m_TexEnvs"]}
        print(f"  Mat PID={o.path_id}: '{tt['m_Name']}' shader={tt['m_Shader']['m_PathID']} texs={texs}")
