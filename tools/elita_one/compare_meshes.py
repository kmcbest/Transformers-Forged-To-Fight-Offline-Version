import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
elita_bundle = ROOT / "assets_redeco" / "elita_one_gs.assetbundle"
arcee_bundle = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"

def inspect_meshes(bundle_path, name):
    print(f"\n==================== MESHES IN {name} ====================")
    env = UnityPy.load(str(bundle_path))
    for obj in env.objects:
        if obj.type.name == "Mesh":
            m = obj.read_typetree()
            m_name = m.get("m_Name")
            verts = m.get("m_VertexData", {}).get("m_VertexCount", 0)
            sms = m.get("m_SubMeshes", [])
            bps = len(m.get("m_BindPose", []))
            hashes = len(m.get("m_BoneNameHashes", []))
            skin = len(m.get("m_Skin", []))
            print(f"Mesh PID {obj.path_id:20d} | Name: {m_name:30s} | Verts: {verts:6d} | SubMeshes: {len(sms)} | BindPoses: {bps} | BoneHashes: {hashes} | Skin: {skin}")
            for idx, sm in enumerate(sms):
                print(f"    Submesh {idx}: firstByte={sm.get('firstByte')}, indexCount={sm.get('indexCount')}, topology={sm.get('topology')}")

inspect_meshes(arcee_bundle, "ARCEE ORIGINAL")
inspect_meshes(elita_bundle, "ELITA ONE CURRENT")
