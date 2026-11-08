import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_grindor_cin_rotf_01":
            aabb = tree.get("m_LocalAABB", {})
            print(f"Grindor Vehicle Mesh: {tree.get('m_Name')}")
            print(f"AABB: {aabb}")
            # check min, max of vertices
            vdata = tree.get("m_VertexData", {})
            print(f"VertexCount: {vdata.get('m_VertexCount')}")
            # Read channels
            # UnityPy mesh read
            m = obj.read()
            verts = m.vertices
            if verts:
                xs = [v[0] for v in verts]
                ys = [v[1] for v in verts]
                zs = [v[2] for v in verts]
                print(f"X range: [{min(xs):.2f}, {max(xs):.2f}] (span={max(xs)-min(xs):.2f})")
                print(f"Y range: [{min(ys):.2f}, {max(ys):.2f}] (span={max(ys)-min(ys):.2f})")
                print(f"Z range: [{min(zs):.2f}, {max(zs):.2f}] (span={max(zs)-min(zs):.2f})")
