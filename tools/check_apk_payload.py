import zipfile

with zipfile.ZipFile("build/Transformers-9.2-offline-blender.apk", "r") as z:
    for info in z.infolist():
        if "payload" in info.filename.lower() or "offline" in info.filename.lower() or "bin" in info.filename.lower():
            print(info.filename, info.file_size, info.date_time)
        if "assets/tftf" in info.filename:
            print(info.filename, info.file_size, info.date_time)
