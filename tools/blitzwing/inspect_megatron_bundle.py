import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
bundle_path = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_gs_leader2015_odr" / "megatron_gs_leader2015.assetbundle"
print(f"Loading {bundle_path}...")
env = UnityPy.load(str(bundle_path))

cab_files = [k for k in env.file.files.keys() if k.lower().startswith("cab-") and "." not in k]
print(f"CAB: {cab_files}")

for obj in env.objects:
    if obj.type.name in ("Mesh", "Material", "Texture2D", "SkinnedMeshRenderer", "GameObject", "AssetBundle"):
        try:
            d = obj.read()
            name = getattr(d, "m_Name", "")
            if obj.type.name == "Mesh":
                print(f"[Mesh] PID: {obj.path_id} | Name: '{name}' | Verts: {len(d.vertices)} | Submeshes: {len(d.submeshes)}")
            elif obj.type.name == "Material":
                print(f"[Material] PID: {obj.path_id} | Name: '{name}'")
            elif obj.type.name == "Texture2D":
                print(f"[Texture2D] PID: {obj.path_id} | Name: '{name}' | Size: {d.image.size if hasattr(d, 'image') else '?'}")
            elif obj.type.name == "SkinnedMeshRenderer":
                tt = obj.read_typetree()
                mesh_ref = tt.get("m_Mesh", {})
                mats = tt.get("m_Materials", [])
                bones = tt.get("m_Bones", [])
                print(f"[SMR] PID: {obj.path_id} | MeshPathID: {mesh_ref.get('m_PathID')} | Bones: {len(bones)} | Mats: {len(mats)}")
            elif obj.type.name == "AssetBundle":
                print(f"[AssetBundle] PID: {obj.path_id} | Name: '{name}'")
        except Exception as e:
            print(f"[{obj.type.name}] PID: {obj.path_id} Error: {e}")
