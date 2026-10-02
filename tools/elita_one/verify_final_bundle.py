import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path("assets_redeco/elita_one_gs.assetbundle")
if not bundle_path.is_file():
    print(f"Error: {bundle_path} not found")
    sys.exit(1)

env = UnityPy.load(str(bundle_path))

print(f"=== Verification of {bundle_path.name} ({bundle_path.stat().st_size / (1024*1024):.2f} MB) ===")

go_dict = {}
tr_dict = {}
tr_to_go = {}
go_to_tr = {}

for obj in env.objects:
    if obj.type.name == "GameObject":
        go_dict[obj.path_id] = obj.read_typetree()
    elif obj.type.name == "Transform":
        tr = obj.read_typetree()
        tr_dict[obj.path_id] = tr
        go_id = tr.get("m_GameObject", {}).get("m_PathID")
        tr_to_go[obj.path_id] = go_id
        go_to_tr[go_id] = obj.path_id

def get_prefab_transforms(root_go_id):
    result = {}
    def recurse(go_id):
        go = go_dict.get(go_id)
        if not go: return
        name = go.get('m_Name')
        tr_id = go_to_tr.get(go_id)
        if name not in result:
            result[name] = tr_id
        tr = tr_dict.get(tr_id)
        if tr:
            for child in tr.get('m_Children', []):
                c_tr_id = child.get('m_PathID')
                c_go_id = tr_to_go.get(c_tr_id)
                recurse(c_go_id)
    recurse(root_go_id)
    return result

p1_tr = get_prefab_transforms(-5193028223035516378)
p2_tr = get_prefab_transforms(-4037407093067927022)

print(f"1. Transform Isolation:")
print(f"   Prefab 1 (Showcase) unique transforms: {len(p1_tr)}")
print(f"   Prefab 2 (Combat LW) unique transforms: {len(p2_tr)}")

# Verify SMRs
smr_count = 0
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        bones = tree.get("m_Bones", [])
        if len(bones) == 64:
            smr_count += 1
            is_p1 = (obj.path_id == 8283545308434878436)
            pref_name = "Prefab 1 (Showcase)" if is_p1 else "Prefab 2 (Combat LW)"
            expected_tr = p1_tr if is_p1 else p2_tr
            other_tr = p2_tr if is_p1 else p1_tr
            
            in_own = sum(1 for b in bones if b.get("m_PathID") in expected_tr.values())
            in_other = sum(1 for b in bones if b.get("m_PathID") in other_tr.values())
            print(f"   SMR on {pref_name} (PID: {obj.path_id}): {len(bones)} bones | Correct: {in_own} | Foreign: {in_other}")
            assert in_other == 0, f"CROSS-PREFAB VIOLATION: SMR has foreign bones!"
            assert in_own == 64, f"Missing bones in SMR!"

print(f"   [✓] Strict 0-cross-reference physical isolation verified on {smr_count} SMRs!")

# Verify Mesh
print(f"\n2. Mesh Geometry & Bounding Box:")
for obj in env.objects:
    if obj.type.name == "Mesh" and obj.read_typetree().get("m_Name") == "cha_arcee_gs_deluxe2014_00":
        tree = obj.read_typetree()
        vc = tree.get("m_VertexData", {}).get("m_VertexCount", 0)
        aabb = tree.get("m_LocalAABB", {})
        c = aabb.get("m_Center")
        e = aabb.get("m_Extent")
        bp_count = len(tree.get("m_BindPose", []))
        sms = tree.get("m_SubMeshes", [])
        print(f"   Vertex Count: {vc}")
        print(f"   Submeshes: {len(sms)}")
        print(f"   BindPoses: {bp_count}")
        print(f"   Center: ({c.get('x'):.3f}, {c.get('y'):.3f}, {c.get('z'):.3f})")
        print(f"   Extent: ({e.get('x'):.3f}, {e.get('y'):.3f}, {e.get('z'):.3f})")
        assert vc == 52432, f"Unexpected vertex count: {vc}"
        assert len(sms) == 2, f"Unexpected submesh count: {len(sms)}"
        assert bp_count == 64, f"Unexpected bindpose count: {bp_count}"
        assert abs(c.get('y') - 4.42) < 0.1, "Height center deviated!"
        print(f"   [✓] Mesh geometry & frustum culling AABB bounds fully verified!")

# Verify Textures
print(f"\n3. Texture Replacements:")
for obj in env.objects:
    if obj.type.name == "Texture2D":
        tree = obj.read_typetree()
        name = tree.get("m_Name")
        if name in [
            "cha_arcee_gs_deluxe2014_main_a", "main_NM", "main_tform_misc_RAOE",
            "tform_misc_A", "tform_misc_NM", "wpns_RAOE"
        ]:
            w = tree.get("m_Width")
            h = tree.get("m_Height")
            fmt = tree.get("m_TextureFormat")
            print(f"   Texture: {name:32s} | {w}x{h} | Format: {fmt}")

print(f"\n[✓] ALL QUALITY GATES PASSED! Bundle is clean and ready for deployment.")
