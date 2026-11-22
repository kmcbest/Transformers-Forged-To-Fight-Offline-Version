import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

bundle_path = r'extracted_apk\assets\assetpack\wheeljack_gs_mp20_odr\wheeljack_gs_mp20.assetbundle'
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == 'GameObject':
        d = obj.read()
        name = getattr(d, 'name', '') or getattr(d, 'm_Name', '')
        if 'wheeljack' in name.lower() and ('mp20' in name.lower() or 'gs' in name.lower()):
            # check if it has Transform with parent=None
            tr = None
            for c in getattr(d, 'm_Components', []):
                try:
                    c_obj = c.read()
                    if c_obj.type.name == 'Transform':
                        tr = c_obj
                        break
                except:
                    pass
            parent = getattr(tr, 'm_Father', None)
            has_parent = False
            if parent:
                try:
                    if parent.path_id != 0:
                        has_parent = True
                except:
                    pass
            if not has_parent:
                print(f"Root Prefab GameObject: '{name}' (path_id={obj.path_id})")
