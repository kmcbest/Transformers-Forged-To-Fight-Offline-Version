# -*- coding: utf-8 -*-
"""
Random encounters generator module for TFTF Revival.
Preserved for future custom game modes and random encounter events.
"""
import random
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
import gamedata

# Pool of 54 non-Sharkticon bots (all playable Autobots and Decepticons)
NON_SHARKTICON_POOL = [
    bid for bid in gamedata.ROSTER if not bid.startswith("sharkticon_")
]

def pick_random_enemy(is_boss=False, pool=None):
    """
    Pick a random enemy with balanced rank and level scaling.
    """
    candidates = pool or NON_SHARKTICON_POOL
    bid = random.choice(candidates)
    if is_boss:
        rank = random.randint(3, 5)
        level = random.randint(15, 30)
        label = "BOSS挑战"
    else:
        rank = random.randint(1, 3)
        level = random.randint(5, 20)
        label = "巡逻遭遇"
    return bid, rank, level, label

def generate_random_mission_encounters(dim=3):
    """
    Generate randomized encounters for all combat nodes on the map.
    """
    encounters = {}
    m_bid, m_rank, m_lvl, m_lab = pick_random_enemy(is_boss=False)
    b_bid, b_rank, b_lvl, b_lab = pick_random_enemy(is_boss=True)
    while b_bid == m_bid:
        b_bid, b_rank, b_lvl, b_lab = pick_random_enemy(is_boss=True)
    
    encounters[1] = (m_bid, False, m_lab, m_rank, m_lvl)
    encounters[2] = (b_bid, True, b_lab, b_rank, b_lvl)
    return encounters

if __name__ == "__main__":
    print(f"Total non-sharkticon pool size: {len(NON_SHARKTICON_POOL)}")
    for i in range(5):
        enc = generate_random_mission_encounters()
        print(f"Simulation {i+1}:")
        print(f"  Node 1: {enc[1]}")
        print(f"  Node 2 (Boss): {enc[2]}")
