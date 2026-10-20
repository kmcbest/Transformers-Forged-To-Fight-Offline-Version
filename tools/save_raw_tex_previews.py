from PIL import Image

nem_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Toxitron\cha_nemesisprime_gs_voyager2015_main_a.png"
opt_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\OptimusPrime\cha_optimusprime_gs_voyager2015_main_a.png"
brain_dir = r"C:\Users\Xiangli496\.gemini\antigravity\brain\76f5ec0f-a15b-490d-aeb0-5237fdbedbfa"

Image.open(nem_path).resize((512, 512)).save(f"{brain_dir}/raw_nemesis_tex.png")
Image.open(opt_path).resize((512, 512)).save(f"{brain_dir}/raw_optimus_tex.png")
print("Saved raw texture previews.")
