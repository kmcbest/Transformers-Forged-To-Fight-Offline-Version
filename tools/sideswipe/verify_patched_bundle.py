import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

BUNDLE_PATH = Path(r"E:\Agent\TFTF-blender\assets_redeco\sideswipe_cin_rotf.assetbundle")

def verify():
    print(f"=== Inspecting Patched Bundle: {BUNDLE_PATH.name} ===")
    env = UnityPy.load(str(BUNDLE_PATH))
    sf = list(env.assets)[0]

    # 1. Fight AOC
    fight_aoc = sf.objects[-2047393535863576714].read_typetree()
    clips = fight_aoc.get("m_Clips", [])
    slot00 = clips[0]
    print(f"Fight AOC Slot 00 (Idle): orig={slot00['m_OriginalClip']} override={slot00['m_OverrideClip']}")
    assert slot00['m_OverrideClip']['m_PathID'] == -8455018533602519118, "Idle clip mismatch!"

    # Check key moves
    slot_m2 = clips[26] # M2
    slot_s1 = clips[49] # S1
    slot_s2 = clips[50] # S2
    slot_s3 = clips[51] # S3
    print(f"Fight AOC Slot 26 (M2): orig={slot_m2['m_OriginalClip']} override={slot_m2['m_OverrideClip']}")
    print(f"Fight AOC Slot 49 (S1): orig={slot_s1['m_OriginalClip']} override={slot_s1['m_OverrideClip']}")
    print(f"Fight AOC Slot 50 (S2): orig={slot_s2['m_OriginalClip']} override={slot_s2['m_OverrideClip']}")
    print(f"Fight AOC Slot 51 (S3): orig={slot_s3['m_OriginalClip']} override={slot_s3['m_OverrideClip']}")

    # 2. Car AOC
    car_aoc = sf.objects[9188181967379678347].read_typetree()
    car_clips = car_aoc.get("m_Clips", [])
    slot63 = car_clips[63]
    print(f"Car AOC Slot 63 (SP3 Car): orig={slot63['m_OriginalClip']} override={slot63['m_OverrideClip']}")
    assert slot63['m_OverrideClip']['m_FileID'] == 5 and slot63['m_OverrideClip']['m_PathID'] == -341215899653024, "Car SP3 clip mismatch!"

    # 3. MatineeData
    mdata = sf.objects[8781936353626196161].read_typetree()
    jstr = mdata.get("jSONData", "")
    has_robot = "cha_barricade_cin_dotm_00" in jstr
    has_car = "cha_barricade_cin_dotm_01" in jstr
    has_old_optimus_robot = "cha_optimus_cin_tf_00" in jstr
    has_old_optimus_car = "cha_optimusprime_cin_tf_01" in jstr
    print(f"MatineeData tracks: has_robot={has_robot}, has_car={has_car}, has_old_optimus_robot={has_old_optimus_robot}, has_old_optimus_car={has_old_optimus_car}")
    assert has_robot and has_car and not has_old_optimus_robot and not has_old_optimus_car, "Matinee tracks invalid!"

    # 4. Matinee AOC
    mat_aoc = sf.objects[-2768898539375720182].read_typetree()
    for item in mat_aoc.get("_overrideControllerList", []):
        if item.get("StateHash") == -1405706489:
            print(f"MatineeAOC Base.Idle: ClipName='{item.get('OverrideClipName')}'")
            assert item.get('OverrideClipName') == "Prefight_Brawler_idle_Megatron", "Matinee Idle clip mismatch!"

    # 5. Check Necro idle clip exists
    assert -8455018533602519118 in sf.objects, "Prefight_Brawler_idle_Megatron not in objects!"
    idle_obj = sf.objects[-8455018533602519118]
    print(f"Necrotronus Idle AnimationClip: name='{idle_obj.read_typetree().get('m_Name')}' class_id={idle_obj.class_id}")

    print("ALL CHECKS PASSED [✓]")

if __name__ == "__main__":
    verify()
