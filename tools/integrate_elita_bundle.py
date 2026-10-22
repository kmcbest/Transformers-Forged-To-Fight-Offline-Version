import os
import shutil
from pathlib import Path
import UnityPy

def integrate_elita():
    redeco_dir = Path(r"E:\Agent\TFTF-blender\assets_redeco")
    target_bundle = redeco_dir / "elita_one_gs.assetbundle"
    backup_bundle = redeco_dir / "elita_one_gs_backup_pre_eyes.assetbundle"
    source_friend_bundle = Path(r"E:\Agent\TFTF-blender\tools\elita_diff\elita_one_gs_friend.assetbundle")

    print(f"[*] Source friend bundle: {source_friend_bundle} ({source_friend_bundle.stat().st_size} bytes)")

    # 1. Backup existing bundle if not already backed up
    if target_bundle.exists() and not backup_bundle.exists():
        shutil.copy2(target_bundle, backup_bundle)
        print(f"[+] Backed up original bundle to: {backup_bundle}")

    # 2. Verify source friend bundle with UnityPy and re-save with packer='lz4' to ensure optimal packaging
    print("[*] Loading and verifying source bundle with UnityPy...")
    env = UnityPy.load(str(source_friend_bundle))

    found_textures = {}
    found_meshes = {}
    found_materials = {}

    for obj in env.objects:
        tname = obj.type.name
        if tname == "Texture2D":
            data = obj.read()
            found_textures[data.m_Name] = (data.m_Width, data.m_Height)
        elif tname == "Mesh":
            data = obj.read()
            found_meshes[data.m_Name] = getattr(data, 'm_Vertices', None)
        elif tname == "Material":
            data = obj.read()
            found_materials[data.m_Name] = data

    print(f"[+] Verified Texture2D count: {len(found_textures)}")
    print(f"    Main Diffuse: {found_textures.get('cha_arcee_gs_deluxe2014_main_a')}")
    print(f"    Main RAOE:    {found_textures.get('main_tform_misc_RAOE')}")
    print(f"    Main NM:      {found_textures.get('main_NM')}")
    print(f"[+] Verified Mesh count: {len(found_meshes)}")
    print(f"[+] Verified Material count: {len(found_materials)}")

    assert "cha_arcee_gs_deluxe2014_main_a" in found_textures
    assert found_textures["cha_arcee_gs_deluxe2014_main_a"] == (1280, 1024)

    # 3. Save to target bundle with LZ4
    print(f"[*] Packaging to {target_bundle} with packer='lz4'...")
    with open(target_bundle, "wb") as f:
        f.write(env.file.save(packer="lz4"))

    print(f"[OK] Successfully integrated Elita AssetBundle! Target size: {target_bundle.stat().st_size} bytes")

    # 4. Copy 1280 textures to tools/elita_one/processed_textures/ for repository assets consistency
    proc_tex_dir = Path(r"E:\Agent\TFTF-blender\tools\elita_one\processed_textures")
    if proc_tex_dir.exists():
        src_tex_dir = Path(r"E:\Agent\TFTF-blender\tools\elita_diff\friend_textures")
        for t_file in ["cha_arcee_gs_deluxe2014_main_a.png", "main_tform_misc_RAOE.png", "main_NM.png"]:
            src_f = src_tex_dir / t_file
            if src_f.exists():
                shutil.copy2(src_f, proc_tex_dir / t_file)
                print(f"[+] Synchronized texture to {proc_tex_dir / t_file}")

if __name__ == "__main__":
    integrate_elita()
