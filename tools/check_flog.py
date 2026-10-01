with open('tools/nativehook/hook.c', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f, 1):
        if 'void flog(' in line or 'flog(' in line and 'FILE' in line:
            print(f"{idx}: {line.strip()}")
            break

# Also view flog definition
with open('tools/nativehook/hook.c', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if 'flog(' in line and ('void' in line or 'static' in line):
        print(f"Found at line {idx}: {line.strip()}")
        for k in range(idx-1, min(idx+30, len(lines))):
            print(f"{k+1}: {lines[k].rstrip()}")
        break
