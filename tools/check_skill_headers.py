with open(r'e:\Agent\TFTF-blender\.agents\skills\tftf_revival\SKILL.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines in SKILL.md: {len(lines)}")
for idx, line in enumerate(lines[:120], 1):
    if line.startswith('#'):
        print(f"Line {idx}: {line.strip()}")
