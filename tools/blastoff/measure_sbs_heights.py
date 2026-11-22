import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from PIL import Image
import numpy as np

img = Image.open(r"E:\Agent\TFTF-blender\renders\blastoff\unity_sbs_00_rest_pose.png")
arr = np.array(img)
# background is (33, 35, 45) approx
# Megatronus is on left (X < 960), Blast Off on right (X > 960)
w = arr.shape[1]
h = arr.shape[0]

diff = np.abs(arr[:, :, :3] - np.array([33, 35, 45])).max(axis=2)
mask = diff > 20

# Left side (Megatronus)
left_mask = mask[:, :w//2]
left_ys, left_xs = np.where(left_mask)
print(f"Megatronus Y range: [{min(left_ys)}, {max(left_ys)}], height={max(left_ys)-min(left_ys)} px")

# Right side (Blast Off)
right_mask = mask[:, w//2:]
right_ys, right_xs = np.where(right_mask)
print(f"Blast Off Y range:   [{min(right_ys)}, {max(right_ys)}], height={max(right_ys)-min(right_ys)} px")
print(f"Ratio Blast Off / Megatronus: {(max(right_ys)-min(right_ys)) / (max(left_ys)-min(left_ys)):.3f}")
