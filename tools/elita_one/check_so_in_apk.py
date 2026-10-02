import zipfile

with zipfile.ZipFile("build/Transformers-9.2-offline-blender.apk", "r") as z:
    so_data = z.read("lib/arm64-v8a/libdothook.so")
    print(f"libdothook.so size in APK: {len(so_data)}")
    print(f"b'elita_one_gs' in libdothook.so: {b'elita_one_gs' in so_data}")
