import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

BRAWL_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\brawl_gs.assetbundle")
env = UnityPy.load(str(BRAWL_BUNDLE))
sf = list(env.assets)[0]

m_r = sf.objects[8927022796776742380].read_typetree()
print("Robot Mesh Submeshes:", len(m_r.get("m_SubMeshes", [])))
for idx, sm in enumerate(m_r.get("m_SubMeshes", [])):
    print(f"  sm[{idx}]: firstVertex={sm.get('firstVertex')}, vertexCount={sm.get('vertexCount')}, indexCount={sm.get('indexCount')}")

m_v = sf.objects[-9025351850097636016].read_typetree()
print("Vehicle Mesh Submeshes:", len(m_v.get("m_SubMeshes", [])))
for idx, sm in enumerate(m_v.get("m_SubMeshes", [])):
    print(f"  sm[{idx}]: firstVertex={sm.get('firstVertex')}, vertexCount={sm.get('vertexCount')}, indexCount={sm.get('indexCount')}")
