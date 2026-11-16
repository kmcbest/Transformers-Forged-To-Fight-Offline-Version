import sys
from pathlib import Path
import UnityPy

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

donor_path = Path("extracted_apk/assets/assetpack/megatron_cin_rotf_odr/megatron_cin_rotf.assetbundle")
brawl_path = Path("assets_redeco/brawl_gs.assetbundle")

print("=== Checking donor vs brawl ===")
env_d = UnityPy.load(str(donor_path))
env_b = UnityPy.load(str(brawl_path))

f_d = [f for f in env_d.files.values() if hasattr(f, 'objects')][0] if any(hasattr(f, 'objects') for f in env_d.files.values()) else list(list(env_d.files.values())[0].files.values())[0]
f_b = [f for f in env_b.files.values() if hasattr(f, 'objects')][0] if any(hasattr(f, 'objects') for f in env_b.files.values()) else list(list(env_b.files.values())[0].files.values())[0]

print(f"Donor objects: {len(f_d.objects)}, Brawl objects: {len(f_b.objects)}")

for k, v in env_d.file.files.items():
    sz = len(v.get_raw_data()) if hasattr(v, 'get_raw_data') else (len(v.data) if hasattr(v, 'data') else 'N/A')
    print(f"Donor entry {k}: {sz} bytes")
for k, v in env_b.file.files.items():
    sz = len(v.get_raw_data()) if hasattr(v, 'get_raw_data') else (len(v.data) if hasattr(v, 'data') else 'N/A')
    print(f"Brawl entry {k}: {sz} bytes")

# Check AssetBundle object
for obj in f_d.objects.values():
    if obj.type.name == "AssetBundle":
        data = obj.read()
        print(f"Donor AssetBundle name: {data.m_Name}")
        print("Donor m_Container:")
        for k, v in data.m_Container:
            print(f"  {k} -> preloadIndex={v.preloadIndex}, preloadSize={v.preloadSize}, asset={v.asset.path_id}")

for obj in f_b.objects.values():
    if obj.type.name == "AssetBundle":
        data = obj.read()
        print(f"AssetBundle name: {data.m_Name}")
        print("m_Container:")
        for k, v in data.m_Container:
            print(f"  {k} -> preloadIndex={v.preloadIndex}, preloadSize={v.preloadSize}, asset={v.asset.path_id}")

print("\n--- Donor Textures ---")
for obj in f_d.objects.values():
    if obj.type.name == "Texture2D":
        data = obj.read()
        sd = getattr(data, "m_StreamData", None)
        sd_info = f"offset={sd.offset}, size={sd.size}, path='{sd.path}'" if sd else "None"
        raw_len = len(getattr(data, "image_data", b""))
        print(f"Donor Tex PID={obj.path_id}: name='{data.m_Name}', format={data.m_TextureFormat}, m_MipCount={data.m_MipCount}, raw_len={raw_len}, StreamData=({sd_info})")
for obj in f_b.objects.values():
    if obj.type.name == "Texture2D":
        data = obj.read()
        sd = getattr(data, "m_StreamData", None)
        sd_info = f"offset={sd.offset}, size={sd.size}, path='{sd.path}'" if sd else "None"
        raw_len = len(getattr(data, "image_data", b""))
        print(f"Tex PID={obj.path_id}: name='{data.m_Name}', size=({data.m_Width}x{data.m_Height}), format={data.m_TextureFormat}, m_MipCount={data.m_MipCount}, raw_len={raw_len}, StreamData=({sd_info})")

# Check SkinnedMeshRenderers in Brawl
print("\n--- Brawl SkinnedMeshRenderers ---")
for obj in f_b.objects.values():
    if obj.type.name == "SkinnedMeshRenderer":
        tt = obj.read_typetree()
        go_pid = tt.get("m_GameObject", {}).get("m_PathID")
        mesh_pid = tt.get("m_Mesh", {}).get("m_PathID")
        bones = tt.get("m_Bones", [])
        root_bone = tt.get("m_RootBone", {}).get("m_PathID")
        enabled = tt.get("m_Enabled")
        print(f"SMR PID={obj.path_id}: go={go_pid}, mesh={mesh_pid}, num_bones={len(bones)}, root={root_bone}, enabled={enabled}")

# Check Meshes in Brawl
print("\n--- Brawl Meshes ---")
for obj in f_b.objects.values():
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        name = tt.get("m_Name")
        bindposes = len(tt.get("m_BindPose", []))
        bone_hashes = len(tt.get("m_BoneNameHashes", []))
        submeshes = len(tt.get("m_SubMeshes", []))
        sd = tt.get("m_StreamData", {})
        print(f"Mesh PID={obj.path_id}: name='{name}', bindposes={bindposes}, bone_hashes={bone_hashes}, submeshes={submeshes}, StreamData={sd}")
