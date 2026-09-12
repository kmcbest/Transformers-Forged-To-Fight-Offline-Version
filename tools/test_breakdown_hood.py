from PIL import Image, ImageDraw
import numpy as np

# Load Decepticon logo
logo_path = r"C:\Users\Xiangli496\.gemini\antigravity\brain\d633472c-6af9-4876-ba8e-7c2b6d54f933\decepticon_logo_clean_1789196964736.jpg"
img = Image.open(logo_path).convert("RGBA")
arr = np.array(img).astype(float)
green = arr[:, :, 1] / 255.0
alpha = np.clip((0.85 - green) / 0.25, 0.0, 1.0) * 255.0
res_arr = np.zeros_like(arr, dtype=np.uint8)
res_arr[:, :, 0] = 110
res_arr[:, :, 1] = 20
res_arr[:, :, 2] = 160
res_arr[:, :, 3] = alpha.astype(np.uint8)
non_empty = np.argwhere(res_arr[:, :, 3] > 10)
ymin, xmin = non_empty.min(axis=0)
ymax, xmax = non_empty.max(axis=0)
full_dec = Image.fromarray(res_arr).crop((xmin, ymin, xmax + 1, ymax + 1))

# Take RIGHT half of Decepticon logo:
# Because x=0 is the center line of the car, and increasing x goes to the right side of the car
W, H = full_dec.size
right_half = full_dec.crop((W // 2, 0, W, H))

# Scale to fit hood
# In Sideswipe orig, half logo was ~110px wide, ~240px high
target_w = 75
target_h = int(right_half.height * (target_w / right_half.width))
half_resized = right_half.resize((target_w, target_h), Image.Resampling.LANCZOS)

# Create test hood canvas
hood_test = Image.new("RGBA", (340, 400), (240, 242, 245, 255))
draw = ImageDraw.Draw(hood_test)

# Half-trapezoid on hood:
# Flat edge at x = 0
# Top edge: y = 20, width = 110
# Bottom edge: y = 350, width = 140
poly = [
    (0, 20),
    (110, 20),
    (140, 350),
    (0, 350),
]
draw.polygon(poly, fill=(235, 60, 30, 255))

# Paste right half of Decepticon logo touching x = 0
# Center vertically in the trapezoid
paste_y = (20 + 350 - target_h) // 2
hood_test.paste(half_resized, (0, paste_y), half_resized)

# Simulate 3D mirror across x = 0:
left_mirrored = hood_test.transpose(Image.FLIP_LEFT_RIGHT)
sim_full_hood = Image.new("RGBA", (hood_test.width * 2, hood_test.height))
sim_full_hood.paste(left_mirrored, (0, 0))
sim_full_hood.paste(hood_test, (hood_test.width, 0))
sim_full_hood.save("scratch_simulated_breakdown_hood.png")

print("Saved scratch_simulated_breakdown_hood.png!")
