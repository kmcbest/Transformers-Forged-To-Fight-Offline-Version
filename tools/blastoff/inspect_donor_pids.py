import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

DONOR_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatronus_gs_kabam_odr\megatronus_gs_kabam.assetbundle")
assert DONOR_BUNDLE.is_file(), f"Not found: {DONOR_BUNDLE}"

env = UnityPy.load(str(DONOR_BUNDLE))

print(f"=== Inspecting {DONOR_BUNDLE.name} ===")
for obj in env.objects:
    t = obj.type.name
    try:
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
    except Exception:
        name = "<?>"
    
    if t in ["Mesh", "Texture2D", "Material", "SkinnedMeshRenderer", "MeshFilter", "MeshRenderer", "AssetBundle"]:
        print(f"[{t}] PID={obj.path_id} name='{name}'")
