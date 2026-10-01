with open('tools/nativehook/hook.c', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f, 1):
        if 'logmsg(' in line and ('"S ' in line or '"O ' in line or '"F ' in line or 'FDS2' in line):
            print(f"{idx}: {line.strip()}")
