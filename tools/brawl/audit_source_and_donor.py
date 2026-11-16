import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

TEX_SRC = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")
MEG_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle")

print("=== ALL TEXTURE FILES IN COMBATICONS TEXTURES DIR ===")
for p in sorted(TEX_SRC.iterdir()):
    print(f"  {p.name}")

print("\n=== ALL SMRs, ROOT GOs & CONTAINER IN MEGATRON BUNDLE ===")
env = UnityPy.load(str(MEG_BUNDLE))
ab = [o for o in env.objects if o.type.name == "AssetBundle"][0].read_typetree()
for k, v in ab["m_Container"]:
    print(f"  Container: '{k}' -> pid={v['asset']['m_PathID']}")

for o in env.objects:
    if o.type.name == "SkinnedMeshRenderer":
        tt = o.read_typetree()
        go_pid = tt["m_GameObject"]["m_PathID"]
        go_name = env.objects[go_pid].read_typetree()["m_Name"] if go_pid in env.objects else "?"
        mesh_pid = tt["m_Mesh"]["m_PathID"]
        mesh_name = env.objects[mesh_pid].read_typetree()["m_Name"] if mesh_pid in env.objects else "?"
        mats = [env.objects[m["m_PathID"]].read_typetree()["m_Name"] for m in tt["m_Materials"] if m["m_PathID"] in env.objects]
        print(f"  SMR pid={o.path_id} go='{go_name}' enabled={tt.get('m_Enabled')} mesh='{mesh_name}'({mesh_pid}) bones={len(tt['m_Bones'])} mats={mats}")
    elif o.type.name == "MeshRenderer":
        tt = o.read_typetree()
        go_pid = tt["m_GameObject"]["m_PathID"]
        go_name = env.objects[go_pid].read_typetree()["m_Name"] if go_pid in env.objects else "?"
        print(f"  MeshRenderer pid={o.path_id} go='{go_name}' enabled={tt.get('m_Enabled')}")
