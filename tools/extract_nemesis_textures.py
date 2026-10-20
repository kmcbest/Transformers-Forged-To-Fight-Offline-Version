import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\assets_ios\nemesisprime_gs_voyager2015_odr\nemesisprime_gs_voyager2015.assetbundle")
out_dir = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Toxitron")
out_dir.mkdir(parents=True, exist_ok=True)

print(f"Loading {bundle_path}...")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "Texture2D":
        data = obj.read()
        name = getattr(data, "m_Name", getattr(data, "name", "unknown"))
        try:
            img = data.image
            save_path = out_dir / f"{name}.png"
            img.save(save_path)
            print(f"Saved texture: {save_path.name} ({img.size}, {img.mode})")
        except Exception as e:
            print(f"Failed to save texture {name}: {e}")
