import os

for root, dirs, files in os.walk('.'):
    if '.git' in root or 'build' in root:
        continue
    for file in files:
        if file.endswith(('.json', '.py', '.txt', '.xml')):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'deliverymode' in content or 'nobundle' in content:
                        print(f"Found in {path}")
            except Exception:
                pass
