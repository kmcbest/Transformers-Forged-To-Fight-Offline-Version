import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)
obj_map = {o.path_id: o for o in env.objects}

# find Transform for GO 7609395052744691237 ('transformed' combat)
for o in env.objects:
    if o.path_id == 7609395052744691237:
        go = o.read_typetree()
        for c in go.get("m_Component", []):
            cid = c.get("component", {}).get("m_PathID")
            if cid in obj_map and obj_map[cid].type.name == "Transform":
                tr = obj_map[cid].read_typetree()
                for ch in tr.get("m_Children", []):
                    ch_id = ch.get("m_PathID")
                    ch_tr = obj_map[ch_id].read_typetree()
                    g_id = ch_tr.get("m_GameObject", {}).get("m_PathID")
                    print(f"Combat transformed child: PID={ch_id} GO='{obj_map[g_id].read_typetree().get('m_Name')}'")
                    if obj_map[g_id].read_typetree().get('m_Name') == "Reference":
                        for gch in ch_tr.get("m_Children", []):
                            gch_id = gch.get("m_PathID")
                            gch_tr = obj_map[gch_id].read_typetree()
                            gg_id = gch_tr.get("m_GameObject", {}).get("m_PathID")
                            print(f"  Combat child of Reference: PID={gch_id} GO='{obj_map[gg_id].read_typetree().get('m_Name')}'")
