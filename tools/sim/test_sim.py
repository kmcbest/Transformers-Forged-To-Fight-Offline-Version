#!/usr/bin/env python3
import ctypes
import json
from pathlib import Path

dll_path = Path(__file__).resolve().parent / "sim_skills.dll"
sim = ctypes.CDLL(str(dll_path))

# Define signatures
sim.sim_init.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
sim.sim_init.restype = ctypes.c_int

sim.sim_tick.argtypes = [ctypes.c_uint32]
sim.sim_tick.restype = None

sim.sim_attack.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
sim.sim_attack.restype = ctypes.c_int

sim.sim_inject_buff.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_float, ctypes.c_int]
sim.sim_inject_buff.restype = ctypes.c_int

sim.sim_get_state_json.argtypes = [ctypes.c_char_p, ctypes.c_int]
sim.sim_get_state_json.restype = ctypes.c_int

sim.sim_pop_logs.argtypes = [ctypes.c_char_p, ctypes.c_int]
sim.sim_pop_logs.restype = ctypes.c_int

sim.sim_pop_floaters.argtypes = [ctypes.c_char_p, ctypes.c_int]
sim.sim_pop_floaters.restype = ctypes.c_int

def get_state():
    buf = ctypes.create_string_buffer(4096)
    sim.sim_get_state_json(buf, 4096)
    return json.loads(buf.value.decode("utf-8"))

def get_logs():
    buf = ctypes.create_string_buffer(8192)
    sim.sim_pop_logs(buf, 8192)
    return json.loads(buf.value.decode("utf-8"))

def get_floaters():
    buf = ctypes.create_string_buffer(4096)
    sim.sim_pop_floaters(buf, 4096)
    return json.loads(buf.value.decode("utf-8"))

print("=== Running Scenario: Movie Optimus vs Bonecrusher ===")
# 1. Initialize match
sim.sim_init(b"optimusprime_cin_tf", b"bonecrusher_cin_rotf", 15000.0, 15000.0, 1000.0, 1000.0)
for log in get_logs():
    print(f"[LOG] {log}")

# 2. Inject 2 stacks of bleed on Optimus (P0)
print("\n--- Injecting 2 stacks of bleed on Optimus (P0) ---")
sim.sim_inject_buff(0, b"dmg_bleed", 6.0, 2)
for log in get_logs():
    print(f"[LOG] {log}")
st0 = get_state()
print(f"P0 HP={st0['p0']['hp']}, Mana={st0['p0']['mana']}, Buffs={st0['p0']['buffs']}")

# 3. Advance time by 500ms
print("\n--- Ticking 500ms (not yet 1000ms) ---")
sim.sim_tick(500)
for log in get_logs():
    print(f"[LOG] {log}")
st1 = get_state()
print(f"P0 HP={st1['p0']['hp']}, Mana={st1['p0']['mana']}, Buffs={st1['p0']['buffs']}")

# 4. Advance time by another 600ms (total 1100ms > 1000ms -> Willpower triggers!)
print("\n--- Ticking 600ms (Clock reaches 2100ms > purify timer) ---")
sim.sim_tick(600)
for log in get_logs():
    print(f"[LOG] {log}")
for flt in get_floaters():
    print(f"[FLOATER] Player {flt['pidx']} Type={flt['type']} Val={flt['val']} Text={flt['text']}")
st2 = get_state()
print(f"P0 HP={st2['p0']['hp']}, Mana={st2['p0']['mana']}, Buffs={st2['p0']['buffs']}")
print(f"Announcement: {st2['announcement']}")

# 5. Optimus now attacks with Heavy Attack (damage = 1000)
print("\n--- Optimus (P0) hits Heavy Attack (1000 dmg) with 1 bleed active ---")
hp_before = st2['p0']['hp']
dmg = sim.sim_attack(0, 4, 0, 1, 0)
for log in get_logs():
    print(f"[LOG] {log}")
for flt in get_floaters():
    print(f"[FLOATER] Player {flt['pidx']} Type={flt['type']} Val={flt['val']} Text={flt['text']}")
st3 = get_state()
hp_after = st3['p0']['hp']
print(f"P0 HP: {hp_before} -> {hp_after} (Change: +{hp_after - hp_before})")
print(f"P1 HP: {st3['p1']['hp']}")
print("\n=== Scenario Verification Complete! ===")
