import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import numpy as np

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_grindor_cin_rotf_01":
            vd = tree.get("m_VertexData", {})
            vcount = vd.get("m_VertexCount", 0)
            data_bytes = bytes(vd.get("m_DataSize", []))
            stride = 40
            verts = []
            for i in range(vcount):
                b = data_bytes[i*stride : i*stride + 12]
                verts.append(np.frombuffer(b, dtype=np.float32))
            verts = np.array(verts)
            
            # Main rotor: X span should be large (-8.7 to +8.7) and Z near 0.16
            main_rotor = verts[(verts[:,1] > 4.0) & (verts[:,2] > -6.0) & (verts[:,2] < 6.0)]
            print(f"Grindor main rotor verts count: {len(main_rotor)}")
            print(f"Main rotor X span: [{main_rotor[:,0].min():.2f}, {main_rotor[:,0].max():.2f}]")
            print(f"Main rotor Y span: [{main_rotor[:,1].min():.2f}, {main_rotor[:,1].max():.2f}]")
            print(f"Main rotor Z span: [{main_rotor[:,2].min():.2f}, {main_rotor[:,2].max():.2f}]")
            print(f"Main rotor center: {main_rotor.mean(axis=0)}")
