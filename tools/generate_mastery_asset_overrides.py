import zipfile
import UnityPy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_APK = ROOT / "com.kabam.bigrobot_9.2.0-123129100_minAPI23(arm64-v8a,armeabi-v7a)(nodpi)_apkmirror.com.apk"
OUT_DIR = ROOT / "assets_overrides" / "bin" / "Data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(BASE_APK, "r") as z:
    # 1. Patch 24fbed0973fe24f3293c3a56dd57e5b0 (MasteryNode)
    print("Patching 24fbed0973fe24f3293c3a56dd57e5b0...")
    raw_node = z.read("assets/bin/Data/24fbed0973fe24f3293c3a56dd57e5b0")
    env = UnityPy.load(raw_node)
    for obj in env.objects:
        if obj.type.name in ["Transform", "RectTransform"]:
            t = obj.read()
            go = t.m_GameObject.read() if hasattr(t, "m_GameObject") else None
            if go and go.m_Name == "Offset":
                print(f"  Old Offset.y: {t.m_LocalPosition.y}")
                t.m_LocalPosition.y = -58.0  # Move down by 18 units
                print(f"  New Offset.y: {t.m_LocalPosition.y}")
                t.save()
                break
    (OUT_DIR / "24fbed0973fe24f3293c3a56dd57e5b0").write_bytes(env.file.save(packer="lz4"))
    print("  Saved to", OUT_DIR / "24fbed0973fe24f3293c3a56dd57e5b0")

    # 2. Patch 6ef56255453a44120879e8531f4f8e94 (MasteryCallout)
    print("Patching 6ef56255453a44120879e8531f4f8e94...")
    raw_callout = z.read("assets/bin/Data/6ef56255453a44120879e8531f4f8e94")
    env2 = UnityPy.load(raw_callout)
    for obj in env2.objects:
        if obj.type.name in ["Transform", "RectTransform"]:
            t = obj.read()
            go = t.m_GameObject.read() if hasattr(t, "m_GameObject") else None
            if go and go.m_Name == "Offset":
                print(f"  Old Offset.y: {t.m_LocalPosition.y}")
                t.m_LocalPosition.y = -53.0  # Move down by 18 units
                print(f"  New Offset.y: {t.m_LocalPosition.y}")
                t.save()
                break
    (OUT_DIR / "6ef56255453a44120879e8531f4f8e94").write_bytes(env2.file.save(packer="lz4"))
    print("  Saved to", OUT_DIR / "6ef56255453a44120879e8531f4f8e94")

    # 3. Patch 945532f09fb3c4f8b8738b3208b4f003 (MasteriesScreenPresentation)
    print("Patching 945532f09fb3c4f8b8738b3208b4f003...")
    raw_screen = z.read("assets/bin/Data/945532f09fb3c4f8b8738b3208b4f003")
    env3 = UnityPy.load(raw_screen)
    for obj in env3.objects:
        if obj.type.name in ["Transform", "RectTransform"]:
            t = obj.read()
            go = t.m_GameObject.read() if hasattr(t, "m_GameObject") else None
            if go and go.m_Name == "Mover":
                print(f"  Old Mover.y: {t.m_LocalPosition.y}")
                t.m_LocalPosition.y = 150.0  # Move up by 30 units (from 120.0 to 150.0)
                print(f"  New Mover.y: {t.m_LocalPosition.y}")
                t.save()
                break
    (OUT_DIR / "945532f09fb3c4f8b8738b3208b4f003").write_bytes(env3.file.save(packer="lz4"))
    print("  Saved to", OUT_DIR / "945532f09fb3c4f8b8738b3208b4f003")

print("\nAll mastery asset overrides created successfully!")
