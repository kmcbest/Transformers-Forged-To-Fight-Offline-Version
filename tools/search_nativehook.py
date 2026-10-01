import os

for root, dirs, files in os.walk('tools/nativehook'):
    for file in files:
        if file.endswith(('.c', '.h', '.cpp')):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for idx, line in enumerate(f, 1):
                    if 'FDS2' in line or 'FDS' in line:
                        print(f"{path}:{idx}: {line.strip()}")
