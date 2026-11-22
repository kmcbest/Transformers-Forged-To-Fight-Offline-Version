import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
# Check official character bundles in extracted_apk
found = 0
for p in (ROOT / "extracted_apk/assets/assetpack").glob("*/*.assetbundle"):
    if not p.name.endswith(".assetbundle") or "portraits" in p.name:
        continue
    try:
        env = UnityPy.load(str(p))
        for o in env.objects:
            if o.type.name == "Transform":
                tt = o.read_typetree()
                # Check if this transform belongs to a GameObject named character_model or Reference
                go_pid = tt.get("m_GameObject", {}).get("m_PathID")
                # find go name
                # just check scale
                ls = tt.get("m_LocalScale")
                if ls and ls["x"] > 0 and abs(ls["x"] - 1.0) > 0.05 and abs(ls["x"] - ls["y"]) < 0.01:
                    print(f"[{p.stem}] Scale = {ls['x']:.3f} on Transform PID={o.path_id}")
                    found += 1
                    if found > 15:
                        break
        if found > 15:
            break
    except Exception:
        pass
