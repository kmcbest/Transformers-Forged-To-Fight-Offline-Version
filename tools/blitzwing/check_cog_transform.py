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
    if o.type.name == "GameObject":
        t = o.read_typetree()
        if t.get("m_Name") in ("transformed", "Reference", "COG"):
            for c in t.get("m_Component", []):
                cid = c.get("component", {}).get("m_PathID")
                if cid in obj_map and obj_map[cid].type.name == "Transform":
                    tr = obj_map[cid].read_typetree()
                    print(f"GO: '{t.get('m_Name')}' (PID={o.path_id}): Pos={tr.get('m_LocalPosition')} Rot={tr.get('m_LocalRotation')} Scale={tr.get('m_LocalScale')}")
