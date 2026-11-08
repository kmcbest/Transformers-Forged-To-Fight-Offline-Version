import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

g_bundle_path = r"E:\Agent\TFTF-blender\toolchain\grindor_anims_registered.assetbundle"
env = UnityPy.load(g_bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        d = obj.read()
        name = getattr(d, 'name', '') or getattr(d, 'm_Name', '')
        if "01" in name:
            tree = obj.read_typetree()
            skin = tree.get("m_Skin", [])
            print(f"Mesh: {name}, m_Skin count: {len(skin)}")
            if not skin:
                # check m_VertexData
                vd = tree.get("m_VertexData", {})
                print(f"VertexData channels: {[c.get('dimension') for c in vd.get('m_Channels', [])]}")
            else:
                for s in skin[:5]:
                    print(s)
