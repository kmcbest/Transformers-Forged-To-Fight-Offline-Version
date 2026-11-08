import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_grindor_cin_rotf_01":
            vd = tree.get("m_VertexData", {})
            channels = vd.get("m_Channels", [])
            print(f"Vertex count: {vd.get('m_VertexCount')}")
            print(f"Data size: {len(vd.get('m_DataSize', []))}")
            for idx, ch in enumerate(channels):
                # stream, offset, format, dimension
                print(f"Channel {idx}: stream={ch.get('stream')}, offset={ch.get('offset')}, format={ch.get('format')}, dim={ch.get('dimension')}")
