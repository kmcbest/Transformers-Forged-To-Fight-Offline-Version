from PIL import Image

nem = Image.open(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Toxitron\cha_nemesisprime_gs_voyager2015_main_a.png")
brain = r"C:\Users\Xiangli496\.gemini\antigravity\brain\76f5ec0f-a15b-490d-aeb0-5237fdbedbfa"

# Crop head region: top-left (0, 0, 300, 300)
head_crop = nem.crop((0, 0, 300, 300))
head_crop.save(f"{brain}/crop_head.png")

# Crop windshield region: (0, 350, 420, 660)
chest_crop = nem.crop((0, 350, 420, 660))
chest_crop.save(f"{brain}/crop_chest.png")

# Crop shoulder region: (650, 200, 900, 450)
shoulder_crop = nem.crop((650, 200, 900, 450))
shoulder_crop.save(f"{brain}/crop_shoulder.png")

print("Crops saved successfully.")
