import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

def inspect_bundle():
    bundle_path = r"E:\Agent\TFTF-blender\assets_redeco\brawl_gs.assetbundle"
    env = UnityPy.load(bundle_path)
    print("=== brawl_gs.assetbundle inspection ===")
    
    print("\n--- Texture2D Objects ---")
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            tt = obj.read_typetree()
            print(f"Texture: {tt.get('m_Name')}, PID: {obj.path_id}, Width: {tt.get('m_Width')}, Height: {tt.get('m_Height')}, Format: {tt.get('m_TextureFormat')}")
            
    print("\n--- Material Objects ---")
    for obj in env.objects:
        if obj.type.name == "Material":
            tt = obj.read_typetree()
            print(f"Material: {tt.get('m_Name')}, PID: {obj.path_id}")
            tex_envs = tt.get('m_SavedProperties', {}).get('m_TexEnvs', {})
            if isinstance(tex_envs, dict):
                for k, v in tex_envs.items():
                    pid = v.get('m_Texture', {}).get('m_PathID') if isinstance(v, dict) else None
                    if pid:
                        print(f"    TexEnv '{k}' -> PID: {pid}")
            elif isinstance(tex_envs, list):
                for item in tex_envs:
                    if isinstance(item, tuple) and len(item) == 2:
                        k, v = item
                        pid = v.get('m_Texture', {}).get('m_PathID') if isinstance(v, dict) else None
                        if pid:
                            print(f"    TexEnv '{k}' -> PID: {pid}")
                    elif isinstance(item, dict):
                        k = item.get('first')
                        pid = item.get('second', {}).get('m_Texture', {}).get('m_PathID')
                        if pid:
                            print(f"    TexEnv '{k}' -> PID: {pid}")

    print("\n--- SkinnedMeshRenderer Objects ---")
    for obj in env.objects:
        if obj.type.name == "SkinnedMeshRenderer":
            tt = obj.read_typetree()
            mesh_pid = tt.get('m_Mesh', {}).get('m_PathID')
            root_pid = tt.get('m_RootBone', {}).get('m_PathID')
            bones_count = len(tt.get('m_Bones', []))
            mats = [m.get('m_PathID') for m in tt.get('m_Materials', [])]
            print(f"SMR PID: {obj.path_id}, Mesh: {mesh_pid}, RootBone: {root_pid}, Bones: {bones_count}, Mats: {mats}")

    print("\n--- Mesh Objects ---")
    for obj in env.objects:
        if obj.type.name == "Mesh":
            tt = obj.read_typetree()
            print(f"Mesh: {tt.get('m_Name')}, PID: {obj.path_id}, Verts: {tt.get('m_VertexData', {}).get('m_VertexCount')}, Submeshes: {len(tt.get('m_SubMeshes', []))}")

if __name__ == "__main__":
    inspect_bundle()
