import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.path_id == -6923321525341018075:
        tt = obj.read_typetree()
        print("Keys:", list(tt.keys()))
        for k in tt.keys():
            v = tt[k]
            if isinstance(v, list):
                print(f" {k}: list of {len(v)}")
            elif isinstance(v, dict):
                print(f" {k}: dict of {list(v.keys())}")
            else:
                print(f" {k}: {v}")
