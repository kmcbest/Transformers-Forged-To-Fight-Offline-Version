import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle"
env = UnityPy.load(bundle_path)
obj_map = {o.path_id: o for o in env.objects}

ac = obj_map.get(-6923321525341018075) # animator_char_fight
tt = ac.read_typetree()
ctrl = tt.get("m_Controller", {})
print("Ctrl keys:", list(ctrl.keys()))
for k, v in ctrl.items():
    if isinstance(v, list):
        print(f" {k}: list len {len(v)}")
        if len(v) > 0 and isinstance(v[0], dict):
            print(f"   item 0 keys: {list(v[0].keys())}")
