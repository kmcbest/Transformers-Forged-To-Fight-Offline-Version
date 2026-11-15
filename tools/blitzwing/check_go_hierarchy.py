import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)

# Find SMR with PID 2138194849323017337 (Tank in showcase)
for o in env.objects:
    if o.path_id == 2138194849323017337:
        smr = o.read_typetree()
        go_pid = smr["m_GameObject"]["m_PathID"]
        print(f"SMR 2138194849323017337 is on GameObject PID {go_pid}")

# Check that GameObject and its Transform
for o in env.objects:
    if o.type.name == "GameObject":
        t = o.read_typetree()
        if t.get("m_Name") in ("transformed", "character_model", "cannon", "transformed_2") or o.path_id in (2138194849323017337, -5385736693872477217):
            print(f"GameObject PID={o.path_id}: name='{t.get('m_Name')}'")
            for comp in t.get("m_Component", []):
                cid = comp.get("component", {}).get("m_PathID")
                print(f"    comp PID: {cid}")

# Check transforms
for o in env.objects:
    if o.type.name == "Transform":
        t = o.read_typetree()
        go_id = t.get("m_GameObject", {}).get("m_PathID")
        if go_id in (-5385736693872477217, 1338737275658030129):
            print(f"Transform PID={o.path_id} on GO {go_id}:")
            print(f"  LocalPos: {t.get('m_LocalPosition')}")
            print(f"  LocalRot: {t.get('m_LocalRotation')}")
            print(f"  LocalScale: {t.get('m_LocalScale')}")
            print(f"  Father: {t.get('m_Father')}")
