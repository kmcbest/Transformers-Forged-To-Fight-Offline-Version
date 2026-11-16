import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
TARN_BUNDLE = ROOT / "assets_redeco" / "tarn_gs.assetbundle"
MEG_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_cin_rotf_odr" / "megatron_cin_rotf.assetbundle"
MOVES_BUNDLE = ROOT / "assets_netflix" / "moves.assetbundle"

print("=== 1. TARN BUNDLE MESH & TEX FORMAT VERIFY ===")
env_t = UnityPy.load(str(TARN_BUNDLE))
sf_t = list(env_t.assets)[0]
for o in env_t.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        if "tarn" in tt["m_Name"]:
            vd = tt["m_VertexData"]
            chans = [(i, c["stream"], c["offset"], c["format"], c["dimension"]) for i, c in enumerate(vd["m_Channels"]) if c["dimension"] > 0]
            print(f"  Mesh '{tt['m_Name']}' vc={vd['m_VertexCount']} bones={len(tt['m_BindPose'])} hashes={len(tt['m_BoneNameHashes'])} chans={chans}")
    elif o.type.name == "Material":
        tt = o.read_typetree()
        if tt["m_Name"] in ("220F843B5128725B8FD90C0E9CF184E91D9E9C9E",) or "Shader" in str(tt):
            pass

print("\n=== 2. MEGATRON EXTERNALS & MOVESET CHECK ===")
env_m = UnityPy.load(str(MEG_BUNDLE))
sf_m = list(env_m.assets)[0]
for i, ext in enumerate(sf_m.externals, 1):
    print(f"  Ext[{i}]: {ext.path}")

ms = sf_m.objects[8437944761280972800].read_typetree()
for m in ms.get("_moves", []):
    print(f"  MegMove: state={m.get('_animStateName'):<22s} name={m.get('_name'):<35s} asset={m.get('_asset')}")

print("\n=== 3. PORTRAITS CHECK ===")
for p in sorted((ROOT / "assets_redeco").glob("*brawl*")):
    print(f"  {p.name:35s} size={p.stat().st_size}")
