from PIL import Image
import numpy as np

img = Image.open(r"C:\Users\Xiangli496\.gemini\antigravity\brain\db8b7cf0-602b-4ceb-a715-2db112ce44ce\unity_elita_arcee_side_by_side.png")
arr = np.array(img)
bg_color = arr[10, 10]
print(f"Image size: {img.size}")
print(f"Background color: {bg_color}")

# Find mask where pixel != bg_color
mask = np.any(np.abs(arr[:, :, :3] - bg_color[:3]) > 10, axis=2)

# Find magenta mask (R > 200, G < 50, B > 200)
magenta_mask = (arr[:, :, 0] > 200) & (arr[:, :, 1] < 50) & (arr[:, :, 2] > 200)

y_indices, x_indices = np.where(mask)
print(f"All foreground bounds: X=[{x_indices.min()}, {x_indices.max()}], Y=[{y_indices.min()}, {y_indices.max()}]")

y_m, x_m = np.where(magenta_mask)
if len(x_m) > 0:
    print(f"Magenta bounds: X=[{x_m.min()}, {x_m.max()}], Y=[{y_m.min()}, {y_m.max()}]")
