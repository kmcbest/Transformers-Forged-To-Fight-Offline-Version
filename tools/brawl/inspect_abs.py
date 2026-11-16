import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

def inspect_ab(path):
    print(f"\n=== Inspecting {path.name} ===")
    env = UnityPy.load(str(path))
    ab_obj = next(o for o in env.objects if o.type.name == "AssetBundle")
    tt = ab_obj.read_typetree()
    print("m_Name:", tt.get("m_Name"))
    print("m_AssetBundleName:", tt.get("m_AssetBundleName"))
    print("Container entries:")
    for k, v in tt.get("m_Container", []):
        print(" ", k, "->", v)

inspect_ab(Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"))
inspect_ab(Path(r"E:\Agent\TFTF-blender\assets_redeco\tarn_gs.assetbundle"))
inspect_ab(Path(r"E:\Agent\TFTF-blender\assets_redeco\brawl_gs.assetbundle"))
