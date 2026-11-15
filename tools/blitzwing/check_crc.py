import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import binascii

def crc(s):
    return binascii.crc32(s.encode('utf-8')) & 0xFFFFFFFF

print("crc32('Reference'):", crc("Reference"))
print("crc32('reference'):", crc("reference"))
print("crc32('Reference/COG'):", crc("Reference/COG"))
