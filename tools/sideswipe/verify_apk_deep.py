import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile
import io
from pathlib import Path
import UnityPy

APKS = [
    Path(r"E:\Agent\TFTF-blender\build\out\Transformers-9.2-offline-blender2.apk"),
    Path(r"E:\Agent\TFTF-blender\build\Transformers-9.2-offline-blender2.apk"),
]

for apk in APKS:
    print(f"=== Deep Verification: {apk} ===")
    assert apk.is_file(), f"Missing {apk}"
    with zipfile.ZipFile(apk, "r") as zf:
        data = zf.read("assets/assetpack/sideswipe_cin_rotf_odr/sideswipe_cin_rotf.assetbundle")
        env = UnityPy.load(io.BytesIO(data))
        sf = list(env.assets)[0]

        # 1. Fight AOC Idle
        faoc = sf.objects[-2047393535863576714].read_typetree()
        slot00 = faoc["m_Clips"][0]
        print(f"  Fight AOC Slot 00 (char_idle): override={slot00['m_OverrideClip']}")
        assert slot00["m_OverrideClip"]["m_PathID"] == -8455018533602519118, "Slot 00 mismatch!"

        # 2. Car AOC SP3
        car_aoc = sf.objects[9188181967379678347].read_typetree()
        slot63 = car_aoc["m_Clips"][63]
        print(f"  Car AOC Slot 63 (SP3 car anim): override={slot63['m_OverrideClip']}")
        assert slot63["m_OverrideClip"]["m_FileID"] == 5 and slot63["m_OverrideClip"]["m_PathID"] == -341215899653024, "Slot 63 mismatch!"

        # 3. MatineeData tracks
        mdata = sf.objects[8781936353626196161].read_typetree()
        jstr = mdata.get("jSONData", "")
        has_robot = "cha_barricade_cin_dotm_00" in jstr
        has_car = "cha_barricade_cin_dotm_01" in jstr
        has_old_optimus_robot = "cha_optimus_cin_tf_00" in jstr
        has_old_optimus_car = "cha_optimusprime_cin_tf_01" in jstr
        print(f"  MatineeData tracks: has_robot={has_robot}, has_car={has_car}, old_optimus={has_old_optimus_robot or has_old_optimus_car}")
        assert has_robot and has_car and not has_old_optimus_robot and not has_old_optimus_car, "Matinee tracks mismatch!"

        # 4. MatineeAOC Idle
        mat_aoc = sf.objects[-2768898539375720182].read_typetree()
        found_mat_idle = False
        for item in mat_aoc.get("_overrideControllerList", []):
            if item.get("StateHash") == -1405706489:
                print(f"  MatineeAOC Base.Idle: ClipName='{item.get('OverrideClipName')}'")
                assert item.get("OverrideClipName") == "Prefight_Brawler_idle_Megatron"
                found_mat_idle = True
                break
        assert found_mat_idle, "MatineeAOC idle not found!"

        # 5. Check libdothook.so
        dh_data = zf.read("lib/arm64-v8a/libdothook.so")
        assert b"cha_barricade_cin_dotm_01" in dh_data, "libdothook.so missing sideswipe string!"
        print(f"  libdothook.so: contains 'cha_barricade_cin_dotm_01' [✓]")

    print(f"  [PASS] {apk.name} verified cleanly!\n")

print("ALL APKS DEEP VERIFIED 100% CLEAN [✓]")
