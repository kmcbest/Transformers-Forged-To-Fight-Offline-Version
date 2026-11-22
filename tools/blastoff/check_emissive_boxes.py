import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np

SRC = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")

def check_box(fname, label, x0, y0, x1, y1):
    im = Image.open(SRC / fname).convert("RGB")
    arr = np.array(im, dtype=np.float32)[y0:y1, x0:x1]
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    m1 = (b > g + 8) & (b > r * 0.85) & (b > 35)
    m2 = (b > g + 3) & (b > r * 0.85) & (b > 20)
    print(f"[{fname} | {label}] box=({x0},{y0},{x1},{y1}): strict={m1.mean()*100:.1f}% loose={m2.mean()*100:.1f}%",
          f"mean_strict={arr[m1].mean(axis=0).round(1) if m1.any() else None}")

# Chest (1024x1024)
check_box("rb_blastoff_chest_cust_matinst.jpg", "Chest Grille LeftHalf", 10, 370, 200, 495)
check_box("rb_blastoff_chest_cust_matinst.jpg", "Chest Grille RightHalf", 200, 370, 365, 495)
check_box("rb_blastoff_chest_cust_matinst.jpg", "Lower Chest Honeycomb", 295, 450, 485, 600)
check_box("rb_blastoff_chest_cust_matinst.jpg", "Ab side purple polys?", 0, 505, 130, 740)
check_box("rb_blastoff_chest_cust_matinst.jpg", "Back turbine ring", 735, 625, 850, 740)

# ArmUp (512x512)
check_box("rb_blastoff_armup_cust_matinst.jpg", "Shoulder Horseshoe Arc", 95, 240, 198, 335)
check_box("rb_blastoff_armup_cust_matinst.jpg", "Shoulder Side Spokes Wheel", 360, 95, 495, 225)
check_box("rb_blastoff_armup_cust_matinst.jpg", "Shoulder Inner Hex", 390, 255, 475, 345)
check_box("rb_blastoff_armup_cust_matinst.jpg", "Shoulder Mid Mesh", 200, 145, 355, 215)

# Legs (1024x1024)
check_box("rb_blastoff_legs_cust_matinst.jpg", "Shin TopRight Strip", 700, 0, 1015, 55)
check_box("rb_blastoff_legs_cust_matinst.jpg", "Shin MidRight Strip1", 695, 175, 755, 245)
check_box("rb_blastoff_legs_cust_matinst.jpg", "Shin MidRight Strip2", 935, 255, 1000, 345)
check_box("rb_blastoff_legs_cust_matinst.jpg", "Shin Center Slit", 425, 430, 470, 520)
check_box("rb_blastoff_legs_cust_matinst.jpg", "Ankle Wheel Hub", 180, 540, 290, 620)

# ArmLo (512x512)
check_box("rb_blastoff_armlo_cust_matinst.jpg", "Forearm Wrist Vent", 400, 465, 475, 512)

# Head (512x512)
check_box("rb_blastoff_head_cust_matinst.jpg", "Head Eyes", 185, 195, 325, 225)
check_box("rb_blastoff_head_cust_matinst.jpg", "Head Rear Vent", 185, 450, 310, 480)

# Veh (1024x1024)
check_box("vh_blastoff_cust_matinst.jpg", "Veh Top Cockpit/Side", 350, 20, 760, 155)
check_box("vh_blastoff_cust_matinst.jpg", "Veh Mid Side Strips", 530, 495, 745, 675)
check_box("vh_blastoff_cust_matinst.jpg", "Veh Thruster Vent", 900, 920, 975, 1010)
