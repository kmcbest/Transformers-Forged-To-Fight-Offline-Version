import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

DONOR_BUNDLE = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
GRIM_BUNDLE = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grimlock_gs_mp08_odr\grimlock_gs_mp08.assetbundle")
MOVES_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")

env = UnityPy.load(str(DONOR_BUNDLE))
sf = list(env.assets)[0]
obj_map = {o.path_id: o for o in env.objects}

print("=== ALL Meshes in Ramjet ===")
for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        print(f"  Mesh PID={o.path_id}: m_Name='{tt.get('m_Name')}', verts={tt.get('m_VertexData', {}).get('m_VertexCount')}")

print("\n=== ALL SkinnedMeshRenderers & MeshRenderers in Ramjet ===")
for o in env.objects:
    if o.type.name in ("SkinnedMeshRenderer", "MeshRenderer", "MeshFilter"):
        tt = o.read_typetree()
        go_pid = tt.get("m_GameObject", {}).get("m_PathID")
        go_name = obj_map[go_pid].read_typetree().get("m_Name") if go_pid in obj_map else "?"
        mesh_pid = tt.get("m_Mesh", {}).get("m_PathID")
        mats = [m.get("m_PathID") for m in tt.get("m_Materials", [])]
        print(f"  {o.type.name} PID={o.path_id} (GO='{go_name}', m_Enabled={tt.get('m_Enabled')}): m_Mesh={mesh_pid}, mats={mats}")

print("\n=== ALL Materials in Ramjet ===")
for o in env.objects:
    if o.type.name == "Material":
        tt = o.read_typetree()
        tex_envs = tt.get("m_SavedProperties", {}).get("m_TexEnvs", [])
        texs = {k: v.get("m_Texture", {}).get("m_PathID") for k, v in tex_envs}
        print(f"  Mat PID={o.path_id}: m_Name='{tt.get('m_Name')}', shader={tt.get('m_Shader', {}).get('m_PathID')}, texs={texs}")

print("\n=== ALL Texture2D in Ramjet ===")
for o in env.objects:
    if o.type.name == "Texture2D":
        tt = o.read_typetree()
        print(f"  Tex PID={o.path_id}: m_Name='{tt.get('m_Name')}', {tt.get('m_Width')}x{tt.get('m_Height')}, fmt={tt.get('m_TextureFormat')}")

print("\n=== ALL GameObjects active state / hierarchy around Renderers ===")
for o in env.objects:
    if o.type.name in ("SkinnedMeshRenderer", "MeshRenderer"):
        tt = o.read_typetree()
        go_pid = tt.get("m_GameObject", {}).get("m_PathID")
        go_tt = obj_map[go_pid].read_typetree()
        print(f"  GO '{go_tt.get('m_Name')}' (PID={go_pid}) m_IsActive={go_tt.get('m_IsActive')}")

print("\n=== Ramjet Heavy Attack in Fight AOC and MoveSet ===")
fight_aoc = obj_map[6432204470035570307].read_typetree()
for i, c in enumerate(fight_aoc.get("m_Clips", [])):
    orig_pid = c["m_OriginalClip"]["m_PathID"]
    ovr_pid = c["m_OverrideClip"]["m_PathID"]
    orig_name = obj_map[orig_pid].read_typetree().get("m_Name") if orig_pid in obj_map else str(orig_pid)
    ovr_name = obj_map[ovr_pid].read_typetree().get("m_Name") if ovr_pid in obj_map else str(ovr_pid)
    if "heavy" in orig_name.lower() or "heavy" in str(ovr_name).lower() or i == 58:
        print(f"  Fight AOC[{i}]: orig='{orig_name}' ({orig_pid}) -> ovr='{ovr_name}' ({ovr_pid})")

moveset = obj_map[-2598790904785067877].read_typetree()
for i, m in enumerate(moveset.get("_moves", [])):
    if "heavy" in m.get("_animStateName", "").lower() or "heavy" in m.get("_name", "").lower() or i == 44:
        print(f"  MoveSet[{i}]: state='{m.get('_animStateName')}', name='{m.get('_name')}', asset={m.get('_asset')}")
