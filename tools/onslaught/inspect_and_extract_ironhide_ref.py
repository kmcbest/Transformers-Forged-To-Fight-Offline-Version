import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
IH_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "ironhide_cin_rotf_odr" / "ironhide_cin_rotf.assetbundle"
IH_ANIMS = ROOT / "toolchain" / "ironhide_anims_registered.assetbundle"
OUT_IH_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Onslaught" / "Ironhide"
OUT_IH_DIR.mkdir(parents=True, exist_ok=True)

print(f"=== 1. LOADING {IH_BUNDLE} ===")
env = UnityPy.load(str(IH_BUNDLE))

id_to_obj = {o.path_id: o for o in env.objects}

def get_name(o):
    try:
        d = o.read()
        return getattr(d, "m_Name", getattr(d, "name", ""))
    except Exception:
        try:
            t = o.read_typetree()
            return t.get("m_Name", "")
        except Exception:
            return ""

for o in env.objects:
    tname = o.type.name
    if tname in ("GameObject", "Avatar", "AnimationClip", "AnimatorController", "Material", "Mesh"):
        nm = get_name(o)
        if tname != "GameObject" or nm in ("Ironhide_CIN_ROTF", "character_model", "transformed") or "cha_ironhide" in nm or "wpn" in nm.lower() or "chop" in nm.lower():
            print(f"  [{tname:20s}] path_id={o.path_id:6d} name='{nm}'")

print("\n=== 2. INSPECTING SKINNEDMESHRENDERERS IN IRONHIDE BUNDLE ===")
for o in env.objects:
    if o.type.name == "SkinnedMeshRenderer":
        tree = o.read_typetree()
        go_pid = tree["m_GameObject"]["m_PathID"]
        go_name = get_name(id_to_obj[go_pid]) if go_pid in id_to_obj else "?"
        mesh_pid = tree["m_Mesh"]["m_PathID"]
        mesh_name = get_name(id_to_obj[mesh_pid]) if mesh_pid in id_to_obj else "None"
        bones = tree.get("m_Bones", [])
        mats = []
        for mp in tree.get("m_Materials", []):
            mpid = mp["m_PathID"]
            mats.append(get_name(id_to_obj[mpid]) if mpid in id_to_obj else str(mpid))
        enabled = tree.get("m_Enabled", 1)
        print(f"  SMR on GO '{go_name}': enabled={enabled}, mesh='{mesh_name}', bones={len(bones)}, mats={mats}")

print("\n=== 3. EXTRACTING ALL IRONHIDE REFERENCE TEXTURES TO UNITY PROJECT ===")
for o in env.objects:
    if o.type.name == "Texture2D":
        data = o.read()
        nm = getattr(data, "m_Name", getattr(data, "name", f"tex_{o.path_id}"))
        try:
            img = data.image
            out_p = OUT_IH_DIR / f"{nm}.png"
            img.save(out_p)
            print(f"  [✓] Saved Texture2D '{nm}' ({img.size[0]}x{img.size[1]}) -> {out_p.name}")
        except Exception as e:
            print(f"  [!] Could not decode Texture2D '{nm}': {e}")

if IH_ANIMS.exists():
    print(f"\n=== 4. INSPECTING {IH_ANIMS.name} ===")
    env_a = UnityPy.load(str(IH_ANIMS))
    for o in env_a.objects:
        if o.type.name == "AnimationClip":
            t = o.read_typetree()
            print(f"  AnimClip: '{t.get('m_Name')}'")
