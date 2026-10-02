import sys
import UnityPy
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path("extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "Mesh":
        data = obj.read()
        name = getattr(data, 'name', getattr(data, 'm_Name', ''))
        if "00" in name or "01" in name:
            print(f"Mesh: {name}")
            print(f"  submesh count: {len(data.m_SubMeshes)}")
            for i, sm in enumerate(data.m_SubMeshes):
                print(f"    submesh[{i}]: firstByte={sm.firstByte}, indexCount={sm.indexCount}, topology={sm.topology}")
