import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
bundle_path = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_gs_leader2015_odr" / "megatron_gs_leader2015.assetbundle"
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        print(f"Mesh PID {obj.path_id}: Name '{tt.get('m_Name')}', VertCount {tt.get('m_VertexData', {}).get('m_VertexCount')}, Submeshes {len(tt.get('m_SubMeshes', []))}, Bones {len(tt.get('m_BoneNameHashes', []))}")
