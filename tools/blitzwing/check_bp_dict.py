import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)

for o in env.objects:
    if o.path_id == -6391917038499381755:
        m = o.read_typetree()
        bp = m["m_BindPose"][1]
        print("Matrix4x4 keys and values:")
        for k, v in sorted(bp.items()):
            print(f"  {k}: {v}")
        break
