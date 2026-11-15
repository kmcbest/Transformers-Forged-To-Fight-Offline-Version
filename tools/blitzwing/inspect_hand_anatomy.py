import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import numpy as np

with open(r'E:\Agent\TFTF-blender\tools\blitzwing\megatron_51_authoritative_bindposes.json', encoding='utf-8') as f:
    d = json.load(f)

# Let's inspect LeftHand and RightHand bones
for side in ['Left', 'Right']:
    print(f"=== {side} Hand Bones ===")
    wrist = np.array(d['bones'][f'{side}Hand']['unity_world_pos'])
    thumb1 = np.array(d['bones'][f'{side}HandThumb1']['unity_world_pos'])
    index1 = np.array(d['bones'][f'{side}HandIndex1']['unity_world_pos'])
    middle1 = np.array(d['bones'][f'{side}HandMiddle1']['unity_world_pos'])
    ring1 = np.array(d['bones'][f'{side}HandRing1']['unity_world_pos'])
    pinky1 = np.array(d['bones'][f'{side}HandPinky1']['unity_world_pos'])
    
    print(f"  Wrist:   {wrist}")
    print(f"  Thumb1:  {thumb1} (rel wrist: {thumb1 - wrist})")
    print(f"  Index1:  {index1} (rel wrist: {index1 - wrist})")
    print(f"  Middle1: {middle1} (rel wrist: {middle1 - wrist})")
    print(f"  Ring1:   {ring1} (rel wrist: {ring1 - wrist})")
    print(f"  Pinky1:  {pinky1} (rel wrist: {pinky1 - wrist})")
