import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

p_bundle = Path(r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
env = UnityPy.load(str(p_bundle))

for o in env.objects:
    if o.path_id == 341294063036995988:
        tt = o.read_typetree()
        print("keys in 341294063036995988:")
        for k in tt:
            print(f"  {k}: type={type(tt[k])}")
            if k == "m_AnimationClips":
                print(f"    clips count={len(tt[k])}")
                for c in tt[k]:
                    print(f"      clip PID={c.get('m_PathID')}")
