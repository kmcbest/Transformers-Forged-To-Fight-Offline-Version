import struct

with open("build/payload_test.bin", "rb") as f:
    data = f.read()

print(f"Total payload size: {len(data)} bytes")

# Search keys
idx = 0
keys = []
while True:
    pos = data.find(b"@userdata:", idx)
    if pos == -1:
        break
    # read key
    end = data.find(b"\x00", pos)
    keys.append(data[pos:end].decode("ascii", errors="ignore"))
    idx = pos + 1

print("Userdata keys:", keys)

# Check hero keys
hero_count = 0
demolishor_found = False
idx = 0
while True:
    pos = data.find(b"@hero:", idx)
    if pos == -1:
        break
    end = data.find(b"\x00", pos)
    k = data[pos:end].decode("ascii", errors="ignore")
    hero_count += 1
    if "demolishor" in k:
        demolishor_found = True
        print(f"Found demolishor hero key: {k}")
    idx = pos + 1

print(f"Total @hero keys: {hero_count}, Demolishor found: {demolishor_found}")
