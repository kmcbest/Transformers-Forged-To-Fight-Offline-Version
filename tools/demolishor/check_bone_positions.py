# -*- coding: utf-8 -*-
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('tools/demolishor/ironhide_80_bones.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

bones_to_check = [
    'Hips', 'Spine', 'Spine1', 'Neck', 'Head',
    'LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand',
    'RightShoulder', 'RightArm', 'RightForeArm', 'RightHand',
    'LeftUpLeg', 'LeftLeg', 'LeftFoot',
    'RightUpLeg', 'RightLeg', 'RightFoot'
]

print("--- Bone World Positions from inverse of m_BindPose ---")
for b in bones_to_check:
    if b in d['bones']:
        m = d['bones'][b]['matrix']
        p = d['bones'][b]['parent']
        print(f"{b:15s}: pos=({m[0][3]:7.2f}, {m[1][3]:7.2f}, {m[2][3]:7.2f})  parent={p}")
    else:
        print(f"{b:15s}: NOT FOUND")
