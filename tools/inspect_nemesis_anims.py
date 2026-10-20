import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\assets_ios\nemesisprime_gs_voyager2015_odr\nemesisprime_gs_voyager2015.assetbundle")
env = UnityPy.load(str(bundle_path))

print("=== ANIMATION CLIPS ===")
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        name = getattr(data, "m_Name", getattr(data, "name", "unknown"))
        print(f"AnimationClip: {name}")
