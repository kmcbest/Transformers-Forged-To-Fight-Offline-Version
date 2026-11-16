import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import json

ROOT = Path(r"E:\Agent\TFTF-blender")

def check_toc(p):
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        print(f"=== {p.parent.name} ===")
        bundles = data.get("bundles", {})
        for bname, binfo in bundles.items():
            print(f"  Bundle: {bname}")
            print(f"    deps: {binfo.get('deps')}")
            print(f"    paths: {binfo.get('paths')}")

check_toc(ROOT / "extracted_apk" / "assets" / "megatron_cin_rotf_odr" / "toc.txt")
check_toc(ROOT / "extracted_apk" / "assets" / "ultramagnus_gs_leader_odr" / "toc.txt")
