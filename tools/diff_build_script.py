import difflib

with open(r'e:\Agent\TFTF-blender\Server\build_phone_apk.py', 'r', encoding='utf-8') as f1:
    l1 = f1.readlines()
with open(r'e:\Agent\TFTF\Server\build_phone_apk.py', 'r', encoding='utf-8') as f2:
    l2 = f2.readlines()

diff = list(difflib.unified_diff(l1, l2, fromfile='blender', tofile='TFTF'))
print('Total diff lines:', len(diff))
for line in diff[:60]:
    print(line.rstrip())
