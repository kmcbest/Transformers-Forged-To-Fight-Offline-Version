import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
donors_dir = ROOT / "extracted_apk" / "assets" / "assetpack"

results = []
for p in donors_dir.glob("*_odr/*.assetbundle"):
    bot_id = p.stem
    try:
        env = UnityPy.load(str(p))
        sf = list(env.assets)[0]
        pref = None
        for o in sf.objects.values():
            if o.type.name == "MonoBehaviour":
                tt = o.read_typetree()
                if "SpecialStagePrefab" in tt or "VictoryStagePrefab" in tt:
                    pref = tt
                    break
        if pref:
            ssp = pref.get("SpecialStagePrefab", {})
            vsp = pref.get("VictoryStagePrefab", {})
            results.append((bot_id, ssp, vsp))
    except Exception as e:
        pass

print(f"Total checked: {len(results)}")
print("\n--- VictoryStagePrefab examples ---")
for bid, ssp, vsp in results[:15]:
    print(f"{bid:30s} | SSP={vsp.get('m_FileID')}:{vsp.get('m_PathID')} | VSP={vsp.get('m_FileID')}:{vsp.get('m_PathID')}")

# Check if any character has SpecialStagePrefab with m_FileID != 0:
ext_ssp = [(bid, ssp) for bid, ssp, vsp in results if ssp.get("m_FileID", 0) != 0]
print(f"\nCharacters with External SpecialStagePrefab ({len(ext_ssp)}):")
for bid, ssp in ext_ssp:
    print(f"  {bid}: {ssp}")

# Check if any character has VictoryStagePrefab with m_FileID != 0:
ext_vsp = [(bid, vsp) for bid, ssp, vsp in results if vsp.get("m_FileID", 0) != 0]
print(f"\nCharacters with External VictoryStagePrefab ({len(ext_vsp)}):")
for bid, vsp in ext_vsp[:15]:
    print(f"  {bid}: {vsp}")
