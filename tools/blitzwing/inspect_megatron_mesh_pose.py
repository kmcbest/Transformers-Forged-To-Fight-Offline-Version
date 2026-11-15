import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r'E:\Agent\TFTF-blender\toolchain\megatron_anims_registered.assetbundle'
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == 'Mesh':
        m = obj.read()
        print(f"Mesh: {m.m_Name}, has vertices: {hasattr(m, 'm_Vertices') and len(m.m_Vertices) if m.m_Vertices else 'no'}")
