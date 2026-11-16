import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        data = obj.read()
        name = getattr(data, 'm_Name', '')
        if "01" in name:
            # Let's read vertices
            # In UnityPy, if m_VertexData is present:
            try:
                raw_mesh = data.read_typetree()
                vd = raw_mesh.get('m_VertexData', {})
                data_size = len(vd.get('m_DataSize', b''))
                print(f"VertexData dataSize: {data_size}")
            except Exception as e:
                print("Error reading typetree:", e)
