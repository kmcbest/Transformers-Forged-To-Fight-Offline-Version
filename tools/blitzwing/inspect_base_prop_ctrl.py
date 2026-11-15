import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle"
env = UnityPy.load(bundle_path)

obj_map = {o.path_id: o for o in env.objects}
ctrl = obj_map.get(341294063036995988)
if ctrl:
    tt = ctrl.read_typetree()
    print("Base Controller Name:", tt.get("m_Name"))
    for l in tt.get("m_Controller", {}).get("m_LayerArray", []):
        print("Layer:", l.get("m_Name"))
