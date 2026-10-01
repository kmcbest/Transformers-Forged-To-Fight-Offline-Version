import json

with open("build/payload_test.bin", "rb") as f:
    data = f.read()

# Let's inspect all keys in payload_test.bin
# How is payload_test.bin structured?
# Let's check Server/export_payload.py to understand header and index!
