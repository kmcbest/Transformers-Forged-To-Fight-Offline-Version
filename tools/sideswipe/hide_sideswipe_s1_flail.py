import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import io
from pathlib import Path
import UnityPy

BUNDLE_PATH = Path("assets_redeco/sideswipe_cin_rotf.assetbundle")
BACKUP_PATH = Path("assets_redeco/sideswipe_cin_rotf.assetbundle.bak")

def patch_sideswipe_flail():
    if not BACKUP_PATH.is_file():
        import shutil
        shutil.copy2(BUNDLE_PATH, BACKUP_PATH)
        print(f"[✓] Created backup at {BACKUP_PATH}")

    env = UnityPy.load(str(BUNDLE_PATH))
    modified_count = 0

    # 1. Update PropsController / CharacterModel MonoBehaviours:
    # Clear _renderers for 'nunchuck' and set Scale to 0
    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            try:
                tt = obj.read_typetree()
                if "_props" in tt:
                    props = tt["_props"]
                    keys = props.get("_serializedKeys", [])
                    vals = props.get("_serializedValues", [])
                    changed = False
                    for k, v in zip(keys, vals):
                        if k == "nunchuck":
                            print(f"[Prop] Found nunchuck in MonoBehaviour PID={obj.path_id}")
                            print(f"  Before: Renderers={v.get('_renderers')}, Scale={v.get('Scale')}")
                            v["_renderers"] = []
                            v["Scale"] = {"x": 0.0, "y": 0.0, "z": 0.0}
                            changed = True
                            print(f"  After:  Renderers={v.get('_renderers')}, Scale={v.get('Scale')}")
                    if changed:
                        obj.save_typetree(tt)
                        modified_count += 1
            except Exception as e:
                pass

    # 2. Update SkinnedMeshRenderers for nunchuck:
    # PathIDs: -5711057110573806536 and -4879794911437009642
    NUNCHUCK_SMR_PIDS = {-5711057110573806536, -4879794911437009642}
    for obj in env.objects:
        if obj.type.name == "SkinnedMeshRenderer" and obj.path_id in NUNCHUCK_SMR_PIDS:
            tt = obj.read_typetree()
            print(f"[SMR] Patching nunchuck SMR PID={obj.path_id}")
            print(f"  Before: Mesh={tt.get('m_Mesh')}, Enabled={tt.get('m_Enabled')}, Mats={tt.get('m_Materials')}")
            tt["m_Mesh"] = {"m_FileID": 0, "m_PathID": 0}
            tt["m_Materials"] = []
            tt["m_Enabled"] = False
            obj.save_typetree(tt)
            modified_count += 1
            print(f"  After:  Mesh={tt.get('m_Mesh')}, Enabled={tt.get('m_Enabled')}, Mats={tt.get('m_Materials')}")

    # 3. Update GameObjects & Transforms:
    # nunchuck root GOs: -4282074790894966000, 5981453158226969972
    # wpns_nunchuck_left GOs: -2204780038870049617, -1614615008613451407
    NUNCHUCK_GO_PIDS = {-4282074790894966000, 5981453158226969972, -2204780038870049617, -1614615008613451407}
    for obj in env.objects:
        if obj.type.name == "GameObject" and obj.path_id in NUNCHUCK_GO_PIDS:
            tt = obj.read_typetree()
            print(f"[GO] Setting m_IsActive=False on GameObject PID={obj.path_id} Name='{tt.get('m_Name')}'")
            tt["m_IsActive"] = False
            obj.save_typetree(tt)
            modified_count += 1

    # nunchuck Transforms: 4796207257227963744, 4994973836030178910
    NUNCHUCK_TRANS_PIDS = {4796207257227963744, 4994973836030178910}
    for obj in env.objects:
        if obj.type.name == "Transform" and obj.path_id in NUNCHUCK_TRANS_PIDS:
            tt = obj.read_typetree()
            print(f"[Transform] Setting Scale=0 on Transform PID={obj.path_id}")
            tt["m_LocalScale"] = {"x": 0.0, "y": 0.0, "z": 0.0}
            obj.save_typetree(tt)
            modified_count += 1

    print(f"\nTotal modified objects: {modified_count}")

    # 4. Save bundle using standard two-stage LZ4 pattern
    print("[*] Saving bundle with packer='lz4'...")
    raw_saved = env.file.save(packer="none")
    env_reload = UnityPy.load(io.BytesIO(raw_saved))
    with open(BUNDLE_PATH, "wb") as f:
        f.write(env_reload.file.save(packer="lz4"))

    new_size_mb = BUNDLE_PATH.stat().st_size / (1024 * 1024)
    print(f"[✓] Successfully saved {BUNDLE_PATH.name} ({new_size_mb:.2f} MB)")

if __name__ == "__main__":
    patch_sideswipe_flail()
