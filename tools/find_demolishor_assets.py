import zipfile
import glob

print("--- Searching in APK ---")
with zipfile.ZipFile("build/Transformers-9.2-offline-blender.apk", "r") as z:
    for name in z.namelist():
        if "demolishor" in name.lower():
            print(f"APK: {name}")

print("\n--- Searching in assets_redeco and other folders ---")
for f in glob.glob("**/*demolishor*", recursive=True):
    print(f"Local: {f}")
