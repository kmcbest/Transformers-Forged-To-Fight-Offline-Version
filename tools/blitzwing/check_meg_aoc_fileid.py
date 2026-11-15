import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

donor_bundle = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(donor_bundle))

for o in env.objects:
    if o.path_id == -3258403100930663047:
        tt = o.read_typetree()
        print("Megatron Tank AOC clips:")
        for c in tt["m_Clips"][:5]:
            print(f"  orig: {c['m_OriginalClip']} -> over: {c['m_OverrideClip']}")
