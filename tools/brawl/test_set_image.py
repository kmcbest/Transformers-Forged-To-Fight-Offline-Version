import sys
from pathlib import Path
from PIL import Image
import UnityPy
from UnityPy.enums import TextureFormat

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

donor_path = Path("extracted_apk/assets/assetpack/megatron_cin_rotf_odr/megatron_cin_rotf.assetbundle")
env = UnityPy.load(str(donor_path))
sf = list(env.files.values())[0] if not hasattr(list(env.files.values())[0], 'files') else list(list(env.files.values())[0].files.values())[0]

TEX_ROBOT_DIFF_PID = 7575930771601290721
obj = sf.objects[TEX_ROBOT_DIFF_PID]
t = obj.read()

png_path = Path("3rd-party-models/Brawl/02_textures/cha_brawl_main_Diffuse.png")
img = Image.open(png_path).convert("RGBA")
r, g, b, _ = img.split()
img = Image.merge("RGBA", (r, g, b, Image.new("L", img.size, 255)))

t.m_Name = "cha_brawl_main_a"
t.m_StreamData.offset = 0
t.m_StreamData.size = 0
t.m_StreamData.path = ""
t.set_image(img, target_format=TextureFormat.RGBA32, mipmap_count=1)
t.save()

# Re-read
t2 = obj.read()
print(f"After set_image: name='{t2.m_Name}', size=({t2.m_Width}x{t2.m_Height}), format={t2.m_TextureFormat}, raw_len={len(t2.image_data)}")
