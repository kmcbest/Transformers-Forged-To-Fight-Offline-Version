import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json

with open(r'E:\Agent\TFTF-blender\3rd-party-models\Brawl\00_donor_reference\donor_summary.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

mesh = d['meshes']['cha_megatron_cin_rotf_00']
avatar_tos = d['avatars']['cha_megatron_cin_rotf_00Avatar']['tos']

print(f"Total bones in robot mesh: {len(mesh['boneHashes'])}")
for idx, h in enumerate(mesh['boneHashes']):
    h_str = str(h)
    bone_path = avatar_tos.get(h_str, "UNKNOWN")
    short_name = bone_path.split('/')[-1] if bone_path != "UNKNOWN" else "UNKNOWN"
    print(f"[{idx:02d}] hash={h:<11} path={bone_path} (name={short_name})")
