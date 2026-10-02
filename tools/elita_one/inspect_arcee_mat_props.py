import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
arcee_bundle = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(str(arcee_bundle))

for obj in env.objects:
    if obj.path_id in [-737396187749761411, 5182645448333425879]:
        mat = obj.read_typetree()
        print(f"Material {mat.get('m_Name')} (PID: {obj.path_id}):")
        props = mat.get("m_SavedProperties", {})
        print("  Floats:", props.get("m_Floats"))
        print("  Colors:", props.get("m_Colors"))
