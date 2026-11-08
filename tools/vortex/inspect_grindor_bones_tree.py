import UnityPy
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "GameObject":
        data = obj.read_typetree()
        gname = data.get("m_Name", "")
        if "grindor_cin_rotf" in gname.lower() and "prefab" not in gname.lower():
            # check components
            print(f"GameObject: {gname}")
    elif obj.type.name == "Mesh":
        data = obj.read_typetree()
        mname = data.get("m_Name", "")
        bp = data.get("m_BindPose", [])
        bnh = data.get("m_BoneNameHashes", [])
        print(f"Mesh: {mname:35s} BindPoses: {len(bp)} Hashes: {len(bnh)}")
