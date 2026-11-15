import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import numpy as np

# Let's inspect the positions of Thumb1, Thumb2, Thumb3 in world space from megatron_thumb_inspection.txt:
# From megatron_thumb_inspection.txt:
# Megatron:
#   LeftHandThumb1: WorldPos: 1.1164, 5.2522, 2.2269
#   LeftHandThumb2: WorldPos: 1.4757, 5.0954, 2.1075
#   LeftHandThumb3: WorldPos: 1.5191, 4.8980, 2.0633
#   LeftHandIndex1: WorldPos: 1.1191, 4.7902, 2.4802
#   LeftHandIndex2: WorldPos: 1.3546, 4.5404, 2.3179
#   LeftHandIndex3: WorldPos: 1.3294, 4.8002, 2.1581

p_t1 = np.array([1.1164, 5.2522, 2.2269])
p_t2 = np.array([1.4757, 5.0954, 2.1075])
p_t3 = np.array([1.5191, 4.8980, 2.0633])

p_i1 = np.array([1.1191, 4.7902, 2.4802])
p_i2 = np.array([1.3546, 4.5404, 2.3179])
p_i3 = np.array([1.3294, 4.8002, 2.1581])

print("Megatron bone positions during Combat Stance Idle:")
print("  Thumb1:", p_t1)
print("  Thumb2:", p_t2)
print("  Thumb3:", p_t3)
print("  Index1:", p_i1)
print("  Index2:", p_i2)
print("  Index3:", p_i3)

print("Thumb segment 1->2 vector:", p_t2 - p_t1)
print("Thumb segment 2->3 vector:", p_t3 - p_t2)
print("Distance Thumb3 to Index2:", np.linalg.norm(p_t3 - p_i2))
print("Distance Thumb3 to Index3:", np.linalg.norm(p_t3 - p_i3))
