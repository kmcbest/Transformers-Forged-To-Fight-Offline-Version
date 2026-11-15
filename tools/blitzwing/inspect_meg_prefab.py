import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
meg_donor = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_gs_leader2015_odr" / "megatron_gs_leader2015.assetbundle"

env = UnityPy.load(str(meg_donor))
for o in env.objects:
    if o.type.name == "GameObject":
        d = o.read_typetree()
        # Find GameObjects that have SMRs or props
        for comp in d.get("m_Component", []):
            cid = comp["component"]["m_PathID"]
            if cid in (2138194849323017337, 4626197738286450028, -8610528988658655013, -4173104293130818967):
                print(f"GO PID={o.path_id}, name='{d['m_Name']}', SMR_PID={cid}")
