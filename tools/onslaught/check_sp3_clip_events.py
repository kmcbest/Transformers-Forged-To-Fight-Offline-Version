import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import UnityPy

env = UnityPy.load(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\ironhide_cin_rotf_odr\ironhide_cin_rotf.assetbundle")
for o in env.objects:
    if o.type.name == "AnimationClip":
        t = o.read_typetree()
        nm = t.get("m_Name", "")
        if "Special_03" in nm or "Heavy" in nm:
            print(f"Clip: {nm} | stopTime={t.get('m_MuscleClip', {}).get('m_StopTime')}")
            for ev in t.get("m_Events", []):
                print(f"  t={ev.get('time'):.3f}s func='{ev.get('functionName')}' str='{ev.get('data')}' int={ev.get('intParameter')} float={ev.get('floatParameter')}")

mb = UnityPy.load(r"E:\Agent\TFTF\assets_netflix\moves.assetbundle")
for o in mb.objects:
    if o.type.name == "TextAsset":
        d = o.read()
        s = getattr(d, "m_Script", "")
        if isinstance(s, bytes):
            s = s.decode("utf-8", errors="ignore")
        if "Ironhide_Normal_attackSpecial_03" in s or ("ironhide" in d.m_Name.lower() and "special" in d.m_Name.lower()):
            print(f"\nMove '{d.m_Name}' references Ironhide special:")
            data = json.loads(s)
            for ev in data.get("moves", {}).get("events", []):
                if any(k in ev.get("type", "").lower() for k in ["transform", "scale", "anim", "vis"]):
                    print(f"  f={ev.get('f')} d={ev.get('d')} type={ev.get('type')} sm={ev.get('sm')} sn={ev.get('sn')} State={ev.get('State')}")
