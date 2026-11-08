import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

g_bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(g_bundle_path)

def dump_node(go, indent=0):
    name = getattr(go, 'm_Name', 'unnamed')
    print(" " * indent + f"- {name}")
    for comp in getattr(go, 'm_Components', []):
        try:
            c = comp.read()
            if c.type.name == "Transform":
                for child_ptr in getattr(c, 'm_Children', []):
                    ch = child_ptr.read()
                    dump_node(ch.m_GameObject.read(), indent + 2)
        except:
            pass

for obj in env.objects:
    if obj.type.name == "GameObject":
        data = obj.read()
        name = getattr(data, 'm_Name', '')
        if "transformed" in name.lower() or "vehicle" in name.lower():
            print(f"Found special GO: '{name}'")
