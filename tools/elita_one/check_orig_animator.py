import sys
import UnityPy
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path("extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "Animator":
        data = obj.read()
        go = data.m_GameObject.read()
        goname = getattr(go, 'name', getattr(go, 'm_Name', ''))
        av_name = ""
        if data.m_Avatar:
            try:
                av = data.m_Avatar.read()
                av_name = getattr(av, 'name', getattr(av, 'm_Name', ''))
            except:
                av_name = "unresolved PPtr"
        print(f"Animator on GameObject: '{goname}', Avatar: '{av_name}'")
