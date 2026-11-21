import sys
import zlib
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

env = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\swoop_gs_deluxe2008.assetbundle")
objs = {o.path_id: o for o in env.objects}

# Find both Main & LW 'transformed' -> 'Reference' Transforms
for root_pid, tag in ((1529847556182042256, "Main"), (-4280993829309278178, "LW")):
    # Walk MonoBehaviours with _props on root
    go = objs[root_pid].read_typetree()
    for c in go["m_Component"]:
        co = objs[c["component"]["m_PathID"]]
        if co.type.name == "MonoBehaviour":
            tt = co.read_typetree()
            if "_props" in tt:
                for k, v in zip(tt["_props"]["_serializedKeys"], tt["_props"]["_serializedValues"]):
                    if k == "transformed":
                        tgo_pid = v["_instance"]["m_PathID"]
                        tgo = objs[tgo_pid].read_typetree()
                        for tc in tgo["m_Component"]:
                            tco = objs[tc["component"]["m_PathID"]]
                            if tco.type.name == "Transform":
                                tr = tco.read_typetree()
                                for ch in tr["m_Children"]:
                                    ch_tr = objs[ch["m_PathID"]].read_typetree()
                                    ch_go = objs[ch_tr["m_GameObject"]["m_PathID"]].read_typetree()
                                    print(f"{tag} transformed child: GO='{ch_go['m_Name']}' trPID={ch['m_PathID']} scale={ch_tr['m_LocalScale']}")

ref_crc = zlib.crc32(b"Reference") & 0xffffffff
print(f"\ncrc32('Reference') = {ref_crc}")
# Check all clips in Swoop + character_anim_procedural for Reference binding
for clip_pid in (7111222233334444555,):
    ct = objs[clip_pid].read_typetree()
    hits = [b for b in ct["m_ClipBindingConstant"]["genericBindings"] if b["path"] == ref_crc]
    print(f"WingFlap Reference bindings: {hits}")
