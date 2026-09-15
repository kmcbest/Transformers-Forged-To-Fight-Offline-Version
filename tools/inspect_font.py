import UnityPy

path = r"E:\Agent\TFTF\extracted_apk\assets\bin\Data\811e9b20e41fd447796b1e264201af71"
try:
    env = UnityPy.load(path)
    print("Objects count:", len(env.objects))
    for obj in env.objects:
        print(f"Type: {obj.type.name}, Name: {getattr(obj, 'name', 'N/A')}")
        if obj.type.name == "Font":
            data = obj.read()
            print("Font m_Name:", data.m_Name)
            if hasattr(data, "m_FontData"):
                print("FontData length:", len(data.m_FontData))
                with open("tools/extracted_font.ttf", "wb") as f:
                    f.write(bytes(data.m_FontData))
                print("Saved tools/extracted_font.ttf")
except Exception as e:
    print("Error:", e)
