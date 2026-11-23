import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
import UnityPy

ROOT_GM = Path(r"E:\Agent\TFTF")

DONORS = [
    ("Cheetor L2", "cheetor_bw_transmetal_odr/cheetor_bw_transmetal.assetbundle", -486271743690878734),
    ("Rhinox L3", "rhinox_gs_voyager2014_odr/rhinox_gs_voyager2014.assetbundle", 93276785253583668),
    ("Rhinox M2", "rhinox_gs_voyager2014_odr/rhinox_gs_voyager2014.assetbundle", -6442010242213229130),
    ("Wheeljack M1", "wheeljack_gs_mp20_odr/wheeljack_gs_mp20.assetbundle", 7265497203347661852),
    ("Kickback M2", "kickback_gs_kabam_odr/kickback_gs_kabam.assetbundle", 221766495520085048),
    ("Mixmaster S1", "mixmaster_cin_rotf_odr/mixmaster_cin_rotf.assetbundle", -7921770726548403079),
    ("Bludgeon S2", "bludgeon_gs_rd20_odr/bludgeon_gs_rd20.assetbundle", -5815229600094096883),
    ("Windblade S1", "windblade_gs_odr/windblade_gs.assetbundle", 4130864494046913653),
]

for label, rel, pid in DONORS:
    p = ROOT_GM / "extracted_apk/assets/assetpack" / rel
    assert p.exists(), f"Missing {p}"
    e = UnityPy.load(str(p))
    objs = {o.path_id: o for o in e.objects}
    assert pid in objs, f"Missing clip PID {pid} in {p.name}"
    tt = objs[pid].read_typetree()
    pptr_map = tt.get("m_ClipBindingConstant", {}).get("pptrCurveMapping", [])
    print(f"  [OK] {label:<14} | {tt['m_Name']:<38} | len={tt['m_MuscleClip']['m_StopTime']:.3f}s | pptr={len(pptr_map)}")
