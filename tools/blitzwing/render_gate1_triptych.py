import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
OUT_DIR = ROOT / "renders" / "blitzwing"

img_robot = Image.open(OUT_DIR / "gate1_robot_preview.png")
img_tank = Image.open(OUT_DIR / "gate1_tank_preview.png")
img_jet = Image.open(OUT_DIR / "gate1_jet_preview.png")

# Crop black borders to make tight panels
def tight_crop(im, pad=20):
    # Convert to grayscale to find bounding box of non-black pixels
    gray = im.convert('L')
    bbox = gray.point(lambda x: 255 if x > 10 else 0).getbbox()
    if bbox:
        x0 = max(0, bbox[0] - pad)
        y0 = max(0, bbox[1] - pad)
        x1 = min(im.width, bbox[2] + pad)
        y1 = min(im.height, bbox[3] + pad)
        return im.crop((x0, y0, x1, y1))
    return im

c_robot = tight_crop(img_robot)
c_tank = tight_crop(img_tank)
c_jet = tight_crop(img_jet)

# Normalize height to 1080
TARGET_H = 900
def resize_to_h(im, h):
    w = int(im.width * (h / im.height))
    return im.resize((w, h), Image.LANCZOS)

r_tank = resize_to_h(c_tank, TARGET_H)
r_robot = resize_to_h(c_robot, TARGET_H)
r_jet = resize_to_h(c_jet, TARGET_H)

total_w = r_tank.width + r_robot.width + r_jet.width + 80
total_h = TARGET_H + 190

canvas = Image.new("RGB", (total_w, total_h), (18, 18, 22))
draw = ImageDraw.Draw(canvas)

# Paste panels: Tank (Left), Robot (Center), Jet (Right)
x_tank = 20
x_robot = x_tank + r_tank.width + 20
x_jet = x_robot + r_robot.width + 20
y_img = 140

canvas.paste(r_tank, (x_tank, y_img))
canvas.paste(r_robot, (x_robot, y_img))
canvas.paste(r_jet, (x_jet, y_img))

# Draw labels & banners
# Title banner
try:
    font_title = ImageFont.truetype("arial.ttf", 36)
    font_sub = ImageFont.truetype("arial.ttf", 20)
    font_panel = ImageFont.truetype("arial.ttf", 26)
except:
    font_title = ImageFont.load_default()
    font_sub = font_title
    font_panel = font_title

title_text = "Transformers: Forged to Fight - BLITZWING (Triple Changer G1 Revival)"
sub_text = "Source: Transformers: Eternal War (PBR Hard-Surface) | Target: Megatron Host + Dual Transformed SMR"

draw.text((total_w // 2, 30), title_text, fill=(240, 240, 255), font=font_title, anchor="mm")
draw.text((total_w // 2, 65), sub_text, fill=(180, 180, 200), font=font_sub, anchor="mm")

# Panel subtitles
draw.text((x_tank + r_tank.width // 2, y_img - 25), "ALT MODE 1: TANK (V1)", fill=(215, 185, 130), font=font_panel, anchor="mm")
draw.text((x_robot + r_robot.width // 2, y_img - 25), "ROBOT MODE (30 Fingers)", fill=(200, 140, 255), font=font_panel, anchor="mm")
draw.text((x_jet + r_jet.width // 2, y_img - 25), "ALT MODE 2: JET (V2)", fill=(130, 200, 255), font=font_panel, anchor="mm")

# Specs at bottom
stats_tank = f"11,540 Verts | PBR Normal + ARM"
stats_robot = f"10,124 Verts | 74 Bones (30 Fingers) | Dual Material PBR"
stats_jet = f"10,050 Verts | PBR Normal + ARM + Canopy Alpha"

draw.text((x_tank + r_tank.width // 2, y_img + TARGET_H + 20), stats_tank, fill=(150, 150, 150), font=font_sub, anchor="mm")
draw.text((x_robot + r_robot.width // 2, y_img + TARGET_H + 20), stats_robot, fill=(150, 150, 150), font=font_sub, anchor="mm")
draw.text((x_jet + r_jet.width // 2, y_img + TARGET_H + 20), stats_jet, fill=(150, 150, 150), font=font_sub, anchor="mm")

out_triptych = OUT_DIR / "gate1_blitzwing_triple_changer_triptych.png"
canvas.save(out_triptych, quality=95)
print(f"Saved triptych showcase to {out_triptych}")
