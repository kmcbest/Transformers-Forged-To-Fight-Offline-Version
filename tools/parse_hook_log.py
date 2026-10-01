with open('tools/tftf_hook.log', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
for i, line in enumerate(lines):
    if not (line.startswith('O ') or line.startswith('F ') or line.startswith('S ') or line.startswith('I ') or line.startswith('E ') or line.startswith('A ')):
        print(f"Line {i}: {line.strip()}")
    elif any(k in line for k in ["HTTP", "auth", "server", "Launcher", "ERROR", "fail", "WARN", "quest", "login"]):
        print(f"Line {i}: {line.strip()}")
