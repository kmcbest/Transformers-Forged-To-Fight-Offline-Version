import sys
import json
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

menv = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")
for o in menv.objects:
    if o.type.name == "TextAsset":
        d = o.read()
        nm = d.m_Name
        if nm.startswith("move_heavy_") and any(k in nm for k in ("starscream", "ramjet", "skywarp", "thundercracker", "dirge", "slipstream", "swoop", "grimlock", "acidstorm", "sunstorm")):
            data = json.loads(d.m_Script)["moves"]
            print(f"\n=== {nm} (events={len(data['events'])}) ===")
            for ev in data["events"]:
                t = ev.get("type")
                if t in ("ActionFlagsMoveEvent", "CameraModifierEvent", "PlayPropAnimatorStateMoveEvent", "PropMoveEvent", "TransformedStateScaleEvent", "TransformMoveEvent", "ProjectileMoveEvent", "AttackWindowMoveEvent"):
                    compact = {k: v for k, v in ev.items() if k in ("f", "d", "sn", "pn", "p", "en", "sm", "State", "po", "fl", "ref", "atr")}
                    print(f"  {t:30s} {compact}")
