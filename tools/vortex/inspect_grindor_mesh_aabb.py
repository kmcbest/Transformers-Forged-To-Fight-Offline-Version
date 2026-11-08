import UnityPy
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        data = obj.read_typetree()
        mname = data.get("m_Name", "")
        aabb = data.get("m_LocalAABB", {})
        center = aabb.get("m_Center", {})
        extent = aabb.get("m_Extent", {})
        print(f"Mesh: {mname:35s} | Center: ({center.get('x',0):.2f}, {center.get('y',0):.2f}, {center.get('z',0):.2f}) | Extent: ({extent.get('x',0):.2f}, {extent.get('y',0):.2f}, {extent.get('z',0):.2f})")
