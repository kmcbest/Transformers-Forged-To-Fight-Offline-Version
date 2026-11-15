import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)
obj_map = {o.path_id: o for o in env.objects}

for o in env.objects:
    if o.path_id == 8396146535644667895:
        m = o.read_typetree()
        bp = m["m_BindPose"]
        for i, p in enumerate(bp):
            # check how close to identity
            # diag: e00, e11, e22, e33
            # trans: e03, e13, e23
            print(f"BP[{i:2d}]: diag=({p['e00']:.3f}, {p['e11']:.3f}, {p['e22']:.3f}, {p['e33']:.3f}) trans=({p['e03']:.3f}, {p['e13']:.3f}, {p['e23']:.3f})")
