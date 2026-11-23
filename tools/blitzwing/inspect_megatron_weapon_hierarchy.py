import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

MEGATRON_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
MOTORMASTER_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\motormaster_gs_combinerwars_odr\motormaster_gs_combinerwars.assetbundle")
WINDBLADE_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\windblade_gs_odr\windblade_gs.assetbundle")
BLUDGEON_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\bludgeon_gs_rd20_odr\bludgeon_gs_rd20.assetbundle")
STARSABER_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\starsaber_gs.assetbundle")


def dump_tr(objs, tr_pid, depth=0, max_d=4):
    if pid := tr_pid:
        if pid not in objs or depth > max_d:
            return
        t = objs[pid].read()
        go = objs[t.m_GameObject.path_id].read() if t.m_GameObject.path_id in objs else None
        name = getattr(go, "m_Name", "?")
        lp = tuple(round(v, 4) for v in (t.m_LocalPosition.x, t.m_LocalPosition.y, t.m_LocalPosition.z))
        lr = tuple(round(v, 4) for v in (t.m_LocalRotation.x, t.m_LocalRotation.y, t.m_LocalRotation.z, t.m_LocalRotation.w))
        ls = tuple(round(v, 4) for v in (t.m_LocalScale.x, t.m_LocalScale.y, t.m_LocalScale.z))
        print("  " * depth + f"{name} GO={t.m_GameObject.path_id} TR={pid} pos={lp} rot={lr} scale={ls}")
        for ch in t.m_Children:
            dump_tr(objs, ch.path_id, depth + 1, max_d)


def check_bundle(path, exact_names):
    if not path.exists():
        print(f"MISSING: {path}")
        return
    env = UnityPy.load(str(path))
    objs = {o.path_id: o for o in env.objects}
    print(f"\n=== {path.name} ===")
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            try:
                t = o.read_typetree()
                if "_props" in t:
                    go = objs[t["m_GameObject"]["m_PathID"]].read() if t["m_GameObject"]["m_PathID"] in objs else None
                    print(f"  PropsController GO={getattr(go, 'm_Name', '?')} PID={o.path_id}:")
                    for p in t["_props"]:
                        print(f"    Name={p.get('Name')} InitFlags={p.get('InitFlags')} Root={p.get('RootPath')} PosOff={p.get('PositionOffset')} RotOff={p.get('RotationOffset')} PropPID={p.get('Prop', {}).get('m_PathID')}")
            except Exception:
                pass
        elif o.type.name == "GameObject":
            go = o.read()
            if go.m_Name.lower() in exact_names:
                tr_pid = None
                for c in go.m_Components:
                    cp = getattr(c, "component", c).path_id
                    if cp in objs and objs[cp].type.name == "Transform":
                        tr_pid = cp
                    elif cp in objs and objs[cp].type.name == "SkinnedMeshRenderer":
                        smr = objs[cp].read()
                        print(f"  SMR {go.m_Name}: root={smr.m_RootBone.path_id} bones={[b.path_id for b in smr.m_Bones]} mesh={smr.m_Mesh.path_id}")
                if tr_pid:
                    dump_tr(objs, tr_pid, 1, 3)


check_bundle(MEGATRON_BUNDLE, {"mace", "staticcannon", "righthand", "lefthand"})
check_bundle(MOTORMASTER_BUNDLE, {"gun", "sword", "lefthand", "righthand"})
check_bundle(WINDBLADE_BUNDLE, {"sword", "righthand"})
check_bundle(BLUDGEON_BUNDLE, {"sword", "righthand"})
check_bundle(STARSABER_BUNDLE, {"gun", "sword", "righthand", "lefthand"})
