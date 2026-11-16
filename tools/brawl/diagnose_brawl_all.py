import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
TEX_SRC = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")
MEG_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_cin_rotf_odr" / "megatron_cin_rotf.assetbundle"
MESH_BUNDLE = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "brawl_mesh.assetbundle"
OUT_BUNDLE = ROOT / "assets_redeco" / "brawl_gs.assetbundle"

print("=== 1. BRAWL SOURCE TEXTURES ===")
for p in sorted(TEX_SRC.iterdir()):
    if "brawl" in p.name.lower() or "interior" in p.name.lower() or "faction" in p.name.lower():
        print(f"  {p.name}")

print("\n=== 2. MEGATRON DONOR MATERIALS & SHADERS ===")
env = UnityPy.load(str(MEG_BUNDLE))
for obj in env.objects:
    if obj.type.name == "Material":
        tt = obj.read_typetree()
        print(f"Material PID={obj.path_id} name='{tt.get('m_Name')}' keywords={tt.get('m_ShaderKeywords')}")
        envs = tt.get("m_SavedProperties", {}).get("m_TexEnvs", [])
        for k, v in envs:
            tex_pid = v.get("m_Texture", {}).get("m_PathID", 0)
            tex_name = ""
            if tex_pid and tex_pid in env.objects:
                pass
            print(f"    {k}: pid={tex_pid} scale={v.get('m_Scale')} off={v.get('m_Offset')}")
        floats = tt.get("m_SavedProperties", {}).get("m_Floats", [])
        fdict = {k: v for k, v in floats}
        print(f"    floats: {fdict}")

print("\n=== 3. FILE TIMESTAMPS ===")
for f in [
    ROOT / "toolchain/unity_build_project/Assets/Brawl/brawl_robot.fbx",
    ROOT / "toolchain/unity_build_project/Assets/Brawl/cha_brawl_gs_00.asset",
    MESH_BUNDLE,
    OUT_BUNDLE,
]:
    if f.exists():
        import datetime
        ts = datetime.datetime.fromtimestamp(f.stat().st_mtime)
        print(f"  {f.name}: size={f.stat().st_size}, mtime={ts}")
    else:
        print(f"  {f.name}: MISSING")
