import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)
obj_map = {o.path_id: o for o in env.objects}

for o in env.objects:
    if o.path_id == -5385736693872477217:
        go = o.read_typetree()
        print("GO cha_megatron_gs_leader2015_01 components:")
        for c in go.get("m_Component", []):
            cid = c.get("component", {}).get("m_PathID")
            print(f"  CID {cid}: {obj_map[cid].type.name if cid in obj_map else 'Unknown'}")

# Check Tank SMR bones
for o in env.objects:
    if o.path_id == 2138194849323017337:
        smr = o.read_typetree()
        print(f"Tank SMR m_RootBone: {smr.get('m_RootBone')}")
        print(f"Tank SMR m_Bones ({len(smr.get('m_Bones', []))}):")
        for i, b in enumerate(smr.get("m_Bones", [])):
            bid = b.get("m_PathID")
            b_tr = obj_map[bid].read_typetree() if bid in obj_map else {}
            b_go_id = b_tr.get("m_GameObject", {}).get("m_PathID")
            b_go_name = obj_map[b_go_id].read_typetree().get("m_Name") if b_go_id in obj_map else "Unknown"
            print(f"  [{i:2d}] PID={bid} GO='{b_go_name}'")
