import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

bundle_path = r'extracted_apk\assets\assetpack\wheeljack_gs_mp20_odr\wheeljack_gs_mp20.assetbundle'
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        d = obj.read()
        go_name = ''
        if d.m_GameObject:
            try:
                go_name = d.m_GameObject.read().m_Name
            except:
                pass
        mesh_name = ''
        if d.m_Mesh:
            try:
                mesh_name = d.m_Mesh.read().m_Name
            except:
                pass
        print(f"SMR (PID={obj.path_id}) on GO '{go_name}' -> Mesh '{mesh_name}'")
