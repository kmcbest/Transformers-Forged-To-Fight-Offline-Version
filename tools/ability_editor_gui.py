#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TFTF 技能与能力可视化桌面编辑器 (Character Abilities Studio)
==========================================================
支持直观查看、修改 78 位英雄的：
1. 特殊攻击 1/2/3 (支持多重效果列表 effects、官方招式名、PUA图标、效果说明)
2. 招牌能力 (名称、PUA图标、触发类别、技能描述)
3. 机体能力 (基础能力卡片、实战机制、自定义触发节如"暴君重拳"、PUA图标、主界面显示开关、说明文案)
4. 协同奖励与羁绊金刚
5. 【游戏内界面实时模拟预览】一键弹出暗色科幻真机高仿界面，所见即所得！

双向存储：实时更新 Server/character_data/{bot_id}.json 明文文件与 Server/tftf_database.db。
运行方式:
    python tools/ability_editor_gui.py
"""

import os
import sys
import re
import json
import sqlite3
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path

# Force UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parent.parent
CHAR_DATA_DIR = ROOT_DIR / "Server" / "character_data"
DB_PATH = ROOT_DIR / "Server" / "tftf_database.db"

# Trigger choices for abilities
TRIGGER_OPTIONS = [
    ("被动 (Passive)", "none"),
    ("重击 (Heavy Attack)", "onHeavyHit"),
    ("所有攻击 (All Attacks)", "onHit"),
    ("基础远程攻击 (Ranged)", "onBasicRange"),
    ("正在格挡 (Block)", "onBlock"),
    ("正在后退 / 回避 (Dodge)", "onDodge"),
    ("特殊攻击 1 (SP1)", "onSpecial1Hit"),
    ("特殊攻击 2 (SP2)", "onSpecial2Hit"),
    ("特殊攻击 3 (SP3)", "onSpecial3Hit"),
    ("当攻击后 (On Struck)", "onStruck"),
]
TRIGGER_LABEL_MAP = {code: label for label, code in TRIGGER_OPTIONS}
TRIGGER_CODE_MAP = {label: code for label, code in TRIGGER_OPTIONS}

CLASS_COLORS = {
    "brawler": "#2ecc71",      # 格斗 (绿)
    "warrior": "#e74c3c",      # 勇士 (红)
    "scout": "#f1c40f",        # 侦察 (黄)
    "tech": "#00d2d3",         # 科技 (青)
    "tactician": "#9b59b6",    # 战术 (紫)
    "demolitions": "#e67e22",  # 爆破 (橙)
}
CLASS_ZH = {
    "brawler": "格斗 (Brawler)",
    "warrior": "勇士 (Warrior)",
    "scout": "侦察 (Scout)",
    "tech": "科技 (Tech)",
    "tactician": "战术 (Tactician)",
    "demolitions": "爆破 (Demolitions)",
}
FACTION_ZH = {
    "autobot": "汽车人 (Autobot)",
    "decepticon": "霸天虎 (Decepticon)",
    "maximal": "巨无霸 (Maximal)",
    "predacon": "原始兽 (Predacon)",
}


def _hex_to_pua_char(pua_str: str) -> str:
    """仅当显式配置了 16 进制字符时转换，绝不猜测。若为空则严格返回空字符串。"""
    if not pua_str:
        return ""
    s = str(pua_str).strip().lower()
    if s.startswith("0x"):
        s = s[2:]
    if s.startswith("\\u"):
        s = s[2:]
    try:
        val = int(s, 16)
        return chr(val) if val > 0 else ""
    except Exception:
        return ""


def _clean_comment(text: str) -> str:
    """去除每一行 // 之后的注释内容，并清理多余空行。保证游戏内说明文本纯净。"""
    if not text:
        return ""
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        if "//" in line:
            line = line.split("//")[0]
        cleaned_lines.append(line.rstrip())
    res = "\n".join(cleaned_lines)
    return re.sub(r'\n{3,}', '\n\n', res).strip()


# =============================================================================
# InGamePreviewWindow: 游戏内界面实时模拟预览窗口 (高仿真 Sci-Fi HUD)
# =============================================================================
class InGamePreviewWindow(tk.Toplevel):
    def __init__(self, parent, bot_data):
        super().__init__(parent)
        self.bot_data = bot_data
        name_zh = bot_data.get("name_zh", "未知英雄")
        bot_id = bot_data.get("bot_id", "")
        self.title(f"🎮 TFTF 游戏内能力界面实时预览 — {name_zh} ({bot_id})")
        self.geometry("1040x840")
        self.minsize(880, 680)
        self.configure(bg="#0a121e")

        self._build_preview_ui()

    def _build_preview_ui(self):
        # 1. Top Header Bar
        header = tk.Frame(self, bg="#0d1b2d", height=70, padx=16, pady=10)
        header.pack(fill=tk.X, side=tk.TOP)

        name_zh = self.bot_data.get("name_zh", "")
        name_en = self.bot_data.get("name_en", "")
        bot_id = self.bot_data.get("bot_id", "")
        bot_class = self.bot_data.get("class", "warrior").lower()
        faction = self.bot_data.get("faction", "").lower()
        class_color = CLASS_COLORS.get(bot_class, "#3498db")
        class_text = CLASS_ZH.get(bot_class, bot_class)
        faction_text = FACTION_ZH.get(faction, faction)

        f_left = tk.Frame(header, bg="#0d1b2d")
        f_left.pack(side=tk.LEFT)

        title_lbl = tk.Label(f_left, text=name_zh, font=("Microsoft YaHei", 18, "bold"), fg="#ffffff", bg="#0d1b2d")
        title_lbl.pack(side=tk.LEFT)

        sub_lbl = tk.Label(f_left, text=f" · {name_en}  [{bot_id}]", font=("Segoe UI", 12), fg="#8fa8c6", bg="#0d1b2d")
        sub_lbl.pack(side=tk.LEFT, padx=(4, 16))

        tag_class = tk.Label(f_left, text=f" {class_text} ", font=("Microsoft YaHei", 9, "bold"), fg="#ffffff", bg=class_color, padx=6, pady=2)
        tag_class.pack(side=tk.LEFT, padx=4)

        tag_faction = tk.Label(f_left, text=f" {faction_text} ", font=("Microsoft YaHei", 9), fg="#e0e0e0", bg="#2c3e50", padx=6, pady=2)
        tag_faction.pack(side=tk.LEFT, padx=4)

        tag_rank = tk.Label(f_left, text=" ★ 5阶 (Rank 5) ", font=("Segoe UI", 9, "bold"), fg="#111111", bg="#f1c40f", padx=6, pady=2)
        tag_rank.pack(side=tk.LEFT, padx=4)

        f_right = tk.Frame(header, bg="#0d1b2d")
        f_right.pack(side=tk.RIGHT)

        btn_close = tk.Button(f_right, text="✕ 关闭 (Close)", font=("Microsoft YaHei", 9), bg="#26384e", fg="#ffffff", activebackground="#34495e", activeforeground="#ffffff", relief="flat", padx=12, pady=4, command=self.destroy)
        btn_close.pack(side=tk.RIGHT)

        # 2. Main Notebook Tabs
        nb_style = ttk.Style(self)
        nb_style.theme_use("clam")
        nb_style.configure("Preview.TNotebook", background="#0a121e", borderwidth=0)
        nb_style.configure("Preview.TNotebook.Tab", background="#152438", foreground="#a0b8d5", font=("Microsoft YaHei", 10, "bold"), padding=[16, 6])
        nb_style.map("Preview.TNotebook.Tab", background=[("selected", "#1c3554")], foreground=[("selected", "#00d2d3")])

        notebook = ttk.Notebook(self, style="Preview.TNotebook")
        notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Tab 1: In-Game Screen Simulation
        tab_sim = tk.Frame(notebook, bg="#0a121e")
        notebook.add(tab_sim, text="  🎮 游戏界面仿真 (In-Game Screen Simulation)  ")
        self._build_simulation_tab(tab_sim, class_color)

        # Tab 2: Wire StatMods Payload Inspect
        tab_wire = tk.Frame(notebook, bg="#0a121e")
        notebook.add(tab_wire, text="  🔧 客户端底层数据流核验 (StatMods & Appearances Wire Diff)  ")
        self._build_wire_tab(tab_wire)

    def _build_simulation_tab(self, parent, class_color):
        # Scrollable Canvas
        canvas = tk.Canvas(parent, bg="#0a121e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scroll_content = tk.Frame(canvas, bg="#0a121e")

        scroll_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_content, anchor="nw", width=990)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mouse wheel support
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # =====================================================================
        # Section A: 主界面能力汇总卡片区 (Main Profile Abilities Cards)
        # =====================================================================
        f_main_sec = tk.LabelFrame(scroll_content, text="  【主界面能力卡片区】 能力会随着升阶而提升 (ShortStringID 非空项渲染于此)  ", font=("Microsoft YaHei", 11, "bold"), fg="#5dade2", bg="#0f1b2b", padx=14, pady=10)
        f_main_sec.pack(fill=tk.X, expand=False, padx=8, pady=(8, 14))

        basic_list = self.bot_data.get("basic_abilities", [])
        if not basic_list:
            # Fallback for legacy format
            basic_list = [a for a in self.bot_data.get("abilities", []) if a.get("show_on_main_screen", False) or a.get("category") == "basic"]

        if not basic_list:
            lbl_empty = tk.Label(f_main_sec, text="(暂无主界面基础能力卡片。可前往'机体能力列表'添加并勾选'主界面显示')", font=("Microsoft YaHei", 9), fg="#7f8c8d", bg="#0f1b2b", pady=8)
            lbl_empty.pack(anchor=tk.W)
        else:
            for b in basic_list:
                card = tk.Frame(f_main_sec, bg="#15263d", bd=1, relief="solid", highlightthickness=1, highlightbackground="#243c5e")
                card.pack(fill=tk.X, pady=4)

                # Accent colored vertical stripe on left
                stripe = tk.Frame(card, bg=class_color, width=6)
                stripe.pack(side=tk.LEFT, fill=tk.Y)

                inner = tk.Frame(card, bg="#15263d", padx=10, pady=6)
                inner.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

                row1 = tk.Frame(inner, bg="#15263d")
                row1.pack(fill=tk.X)

                pua_hex = b.get("pua_icon", "").strip()
                pua_char = _hex_to_pua_char(pua_hex)
                icon_display = f"[{pua_hex}] " if pua_hex else ""

                lbl_c_title = tk.Label(row1, text=f"{icon_display}{b.get('title_zh', '')}", font=("Microsoft YaHei", 12, "bold"), fg="#ffffff", bg="#15263d")
                lbl_c_title.pack(side=tk.LEFT)

                lbl_rank = tk.Label(row1, text="5", font=("Segoe UI", 12, "bold"), fg="#f1c40f", bg="#15263d")
                lbl_rank.pack(side=tk.RIGHT, padx=6)

                desc = _clean_comment(b.get("desc_zh", ""))
                lbl_desc = tk.Label(inner, text=desc, font=("Microsoft YaHei", 9), fg="#cfdbe8", bg="#15263d", wraplength=900, justify=tk.LEFT)
                lbl_desc.pack(anchor=tk.W, pady=(2, 0))

        # =====================================================================
        # Section B: 详细能力弹窗仿真 (In-Game Ability Modal Dialog)
        # =====================================================================
        lbl_modal_hint = tk.Label(scroll_content, text="▼ 点击主界面能力卡片后弹出的官方【技能详情】全屏浮层仿真 (对应原版截图样式) ▼", font=("Microsoft YaHei", 10, "bold"), fg="#f39c12", bg="#0a121e")
        lbl_modal_hint.pack(anchor=tk.W, padx=10, pady=(6, 4))

        # Glowing cyan outline modal container
        modal_frame = tk.Frame(scroll_content, bg="#0d1827", bd=2, relief="solid", highlightthickness=2, highlightbackground="#38a3ff")
        modal_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 16))

        # Modal Title Bar
        m_bar = tk.Frame(modal_frame, bg="#14263e", height=36, padx=12, pady=6)
        m_bar.pack(fill=tk.X)
        tk.Label(m_bar, text="技能详情 (Ability Details)", font=("Microsoft YaHei", 11, "bold"), fg="#ffffff", bg="#14263e").pack(side=tk.LEFT)
        tk.Label(m_bar, text="✕", font=("Segoe UI", 11, "bold"), fg="#7f9bb9", bg="#14263e").pack(side=tk.RIGHT, padx=4)

        m_content = tk.Frame(modal_frame, bg="#0d1827", padx=16, pady=12)
        m_content.pack(fill=tk.BOTH, expand=True)

        # 1. Signature Ability
        sig = self.bot_data.get("signature", {})
        sig_title = sig.get("title_zh") or sig.get("title_en")
        if sig_title:
            f_sig = tk.Frame(m_content, bg="#0d1827")
            f_sig.pack(fill=tk.X, pady=(0, 10))

            tk.Label(f_sig, text="★ 招牌能力", font=("Microsoft YaHei", 12, "bold"), fg="#ffcc00", bg="#0d1827").pack(anchor=tk.W)
            sig_tr = sig.get("ui_trigger", "none")
            sig_tr_label = TRIGGER_LABEL_MAP.get(sig_tr, "被动") if sig_tr == "none" else sig_tr
            tk.Label(f_sig, text=f"{sig_title} ({sig_tr_label})", font=("Microsoft YaHei", 10, "bold"), fg="#5dade2", bg="#0d1827").pack(anchor=tk.W, padx=(8, 0))

            sig_pua = sig.get("pua_icon", "").strip()
            sig_pua_prefix = f"[{sig_pua}] " if sig_pua else "• "
            sig_desc = _clean_comment(sig.get("desc_zh", ""))
            tk.Label(f_sig, text=f"  {sig_pua_prefix}{sig_desc}", font=("Microsoft YaHei", 9), fg="#e0e8f0", bg="#0d1827", wraplength=880, justify=tk.LEFT).pack(anchor=tk.W, padx=(12, 0), pady=(2, 0))

            tk.Frame(m_content, bg="#1e324d", height=1).pack(fill=tk.X, pady=6)

        # 2. Game Abilities (Grouped by ui_trigger)
        game_list = self.bot_data.get("game_abilities", [])
        if not game_list:
            # Fallback for legacy
            game_list = [a for a in self.bot_data.get("abilities", []) if not a.get("show_on_main_screen", False) and a.get("category") != "basic"]

        # Group by trigger
        grouped_abilities = {}
        for ab in game_list:
            tr = ab.get("ui_trigger") or ab.get("title_zh") or "被动"
            # If standard code, map to display
            if tr in TRIGGER_LABEL_MAP:
                tr_display = TRIGGER_LABEL_MAP[tr].split(" ")[0]
            else:
                tr_display = tr
            grouped_abilities.setdefault(tr_display, []).append(ab)

        for tr_name, ab_items in grouped_abilities.items():
            f_group = tk.Frame(m_content, bg="#0d1827")
            f_group.pack(fill=tk.X, pady=4)

            tk.Label(f_group, text=tr_name, font=("Microsoft YaHei", 11, "bold"), fg="#ffffff", bg="#0d1827").pack(anchor=tk.W)

            for ab in ab_items:
                p_hex = ab.get("pua_icon", "").strip()
                p_tag = f"[{p_hex}] " if p_hex else "• "
                c_desc = _clean_comment(ab.get("desc_zh", ""))
                tk.Label(f_group, text=f"  {p_tag}{c_desc}", font=("Microsoft YaHei", 9), fg="#d2dce6", bg="#0d1827", wraplength=880, justify=tk.LEFT).pack(anchor=tk.W, padx=(10, 0), pady=1)

        if grouped_abilities:
            tk.Frame(m_content, bg="#1e324d", height=1).pack(fill=tk.X, pady=6)

        # 3. Special Attacks (SP1 ~ SP3)
        specials = self.bot_data.get("special_attacks", {})
        for idx in (1, 2, 3):
            cat = f"sp{idx}"
            sp_data = specials.get(cat, {})
            if not sp_data:
                continue

            sp_name = sp_data.get("name_zh") or f"特殊攻击 {idx}"
            sp_name_en = sp_data.get("name_en", "")
            effects = sp_data.get("effects", [])

            f_sp = tk.Frame(m_content, bg="#0d1827")
            f_sp.pack(fill=tk.X, pady=4)

            title_str = f"特殊攻击 {idx}: {sp_name}" + (f" ({sp_name_en})" if sp_name_en else "")
            tk.Label(f_sp, text=title_str, font=("Microsoft YaHei", 11, "bold"), fg="#63cdda", bg="#0d1827").pack(anchor=tk.W)

            if effects:
                for eff in effects:
                    eff_title = eff.get("title_zh", "")
                    eff_pua = eff.get("pua_icon", "").strip()
                    eff_desc = _clean_comment(eff.get("desc_zh", ""))
                    pua_tag = f"[{eff_pua}] " if eff_pua else "• "
                    title_prefix = f"【{eff_title}】 " if eff_title and eff_title != sp_name else ""
                    tk.Label(f_sp, text=f"  {pua_tag}{title_prefix}{eff_desc}", font=("Microsoft YaHei", 9), fg="#cfdbe8", bg="#0d1827", wraplength=880, justify=tk.LEFT).pack(anchor=tk.W, padx=(10, 0), pady=1)
            else:
                single_desc = _clean_comment(sp_data.get("desc_zh", ""))
                p_hex = sp_data.get("pua_icon", "").strip()
                pua_tag = f"[{p_hex}] " if p_hex else "• "
                if single_desc:
                    tk.Label(f_sp, text=f"  {pua_tag}{single_desc}", font=("Microsoft YaHei", 9), fg="#cfdbe8", bg="#0d1827", wraplength=880, justify=tk.LEFT).pack(anchor=tk.W, padx=(10, 0), pady=1)

        # 4. Synergies
        synergies = self.bot_data.get("synergies", [])
        if synergies:
            tk.Frame(m_content, bg="#1e324d", height=1).pack(fill=tk.X, pady=6)
            f_syn = tk.Frame(m_content, bg="#0d1827")
            f_syn.pack(fill=tk.X, pady=4)

            tk.Label(f_syn, text="🔗 机体协同 (Synergies)", font=("Microsoft YaHei", 11, "bold"), fg="#b39ddb", bg="#0d1827").pack(anchor=tk.W)
            for syn in synergies:
                h_str = ", ".join(syn.get("bonus_heroes", []))
                s_title = syn.get("title_zh", "")
                s_desc = _clean_comment(syn.get("desc_zh", ""))
                tk.Label(f_syn, text=f"  • 与 [{h_str}]: {s_title} — {s_desc}", font=("Microsoft YaHei", 9), fg="#d2dce6", bg="#0d1827", wraplength=880, justify=tk.LEFT).pack(anchor=tk.W, padx=(10, 0), pady=1)

    def _build_wire_tab(self, parent):
        # Calculate real StatMods and Appearances like character_profiles.py does
        f_top = tk.Frame(parent, bg="#0a121e", padx=10, pady=8)
        f_top.pack(fill=tk.X)

        tk.Label(f_top, text="下方列表展示 Server/character_profiles.py 实时生成的客户端底层 StatModifiers 与 Appearances 数据结构：", font=("Microsoft YaHei", 10), fg="#a0b8d5", bg="#0a121e").pack(anchor=tk.W)

        # Treeview
        tree_frame = tk.Frame(parent, bg="#0a121e", padx=10, pady=4)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "appr_id", "uit", "s_main", "l_detail", "pua", "preview")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=16)
        tree.heading("id", text="StatMod ID")
        tree.heading("appr_id", text="AppearanceID")
        tree.heading("uit", text="触发节 (uit)")
        tree.heading("s_main", text="主界面卡片 (s)")
        tree.heading("l_detail", text="弹窗说明 (l)")
        tree.heading("pua", text="PUA 图标")
        tree.heading("preview", text="文本内容预览")

        tree.column("id", width=160)
        tree.column("appr_id", width=180)
        tree.column("uit", width=130)
        tree.column("s_main", width=90, anchor="center")
        tree.column("l_detail", width=90, anchor="center")
        tree.column("pua", width=70, anchor="center")
        tree.column("preview", width=360)

        t_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=t_scroll.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        t_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Generate wire mods
        bot_id = self.bot_data.get("bot_id", "bot")
        wire_items = []

        # Sig
        sig = self.bot_data.get("signature", {})
        if sig.get("title_zh") or sig.get("title_en"):
            s_title = sig.get("title_zh") or sig.get("title_en")
            s_desc = _clean_comment(sig.get("desc_zh", ""))
            wire_items.append((
                f"sig_{bot_id}", f"appr_sig_{bot_id}",
                sig.get("ui_trigger", "none"),
                "✔ 是", "✔ 是", sig.get("pua_icon", ""),
                f"【招牌】{s_title}: {s_desc}"
            ))

        # Basic
        for idx, b in enumerate(self.bot_data.get("basic_abilities", [])):
            b_title = b.get("title_zh") or b.get("title_en")
            b_desc = _clean_comment(b.get("desc_zh", ""))
            wire_items.append((
                f"ability_{bot_id}_{idx}", f"appr_ability_{bot_id}_{idx}",
                "none",
                "✔ 是", "✖ 否 (不污染)", b.get("pua_icon", ""),
                f"【主卡】{b_title}: {b_desc}"
            ))

        # Game
        b_count = len(self.bot_data.get("basic_abilities", []))
        for g_idx, g in enumerate(self.bot_data.get("game_abilities", [])):
            m_idx = b_count + g_idx
            g_title = g.get("title_zh") or g.get("title_en")
            g_desc = _clean_comment(g.get("desc_zh", ""))
            tr = g.get("ui_trigger") or g_title
            wire_items.append((
                f"ability_{bot_id}_{m_idx}", f"appr_ability_{bot_id}_{m_idx}",
                tr,
                "✖ 否 (不污染)", "✔ 是", g.get("pua_icon", ""),
                f"【实战】[{tr}] {g_title}: {g_desc}"
            ))

        # Specials
        specials = self.bot_data.get("special_attacks", {})
        for sp_idx, cat in enumerate(["sp1", "sp2", "sp3"], start=1):
            sp_data = specials.get(cat, {})
            if not sp_data:
                continue
            sp_name = sp_data.get("name_zh") or f"SP{sp_idx}"
            effects = sp_data.get("effects", [])
            if not effects and sp_data.get("desc_zh"):
                effects = [{"title_zh": sp_name, "desc_zh": sp_data.get("desc_zh"), "pua_icon": sp_data.get("pua_icon", "")}]
            for eff_idx, eff in enumerate(effects):
                eff_name = eff.get("title_zh") or sp_name
                eff_desc = _clean_comment(eff.get("desc_zh", ""))
                wire_items.append((
                    f"sp_ui_{bot_id}_{sp_idx}_{eff_idx}", f"appr_sp_ui_{bot_id}_{sp_idx}_{eff_idx}",
                    f"onSpecial{sp_idx}Hit",
                    "✖ 否", "✔ 是", eff.get("pua_icon", ""),
                    f"【SP{sp_idx}】{sp_name} -> {eff_name}: {eff_desc}"
                ))

        for row in wire_items:
            tree.insert("", tk.END, values=row)


# =============================================================================
# AbilityStudioApp: 主编辑器应用
# =============================================================================
class AbilityStudioApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TFTF 技能与能力可视化编辑器 — Character Abilities Studio")
        self.geometry("1180x820")
        self.minsize(1020, 700)

        # Apply clean ttk style
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.all_bots = []
        self.filtered_bots = []
        self.current_bot_id = None
        self.current_bot_data = None
        self.is_dual_track = True

        # In-memory SP effects data: {1: [effects], 2: [effects], 3: [effects]}
        self.sp_effects = {1: [], 2: [], 3: []}

        self._load_all_bots_metadata()
        self._build_ui()
        self._populate_bot_list()

        # Keyboard shortcuts
        self.bind("<Control-s>", lambda e: self._save_current_bot())
        self.bind("<Control-p>", lambda e: self._open_in_game_preview())

    def _load_all_bots_metadata(self):
        """加载所有 78 位机器人的列表索引。"""
        self.all_bots.clear()
        if not CHAR_DATA_DIR.exists():
            messagebox.showerror("错误", f"找不到角色目录: {CHAR_DATA_DIR}")
            return

        for p in sorted(CHAR_DATA_DIR.glob("*.json")):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    d = json.load(f)
                self.all_bots.append({
                    "bot_id": d.get("bot_id", p.stem),
                    "name_zh": d.get("name_zh", ""),
                    "name_en": d.get("name_en", ""),
                    "faction": d.get("faction", ""),
                    "class": d.get("class", ""),
                    "path": p
                })
            except Exception as e:
                print(f"Error reading {p}: {e}")

        # Sort by Chinese name / bot_id
        self.all_bots.sort(key=lambda x: (x["name_zh"] or x["bot_id"]))
        self.filtered_bots = list(self.all_bots)

    def _build_ui(self):
        # Main PanedWindow (Left: Roster, Right: Editor)
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # =====================================================================
        # LEFT PANEL: Bot Roster Browser
        # =====================================================================
        left_frame = ttk.Frame(paned, width=280)
        paned.add(left_frame, weight=0)

        # Search bar
        search_frame = ttk.LabelFrame(left_frame, text="检索英雄 (Filter)", padding=6)
        search_frame.pack(fill=tk.X, padx=4, pady=2)

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_changed)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X)

        # Faction filter
        fac_frame = ttk.Frame(search_frame)
        fac_frame.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(fac_frame, text="阵营:").pack(side=tk.LEFT)
        self.fac_var = tk.StringVar(value="全部")
        fac_combo = ttk.Combobox(fac_frame, textvariable=self.fac_var, state="readonly", width=12)
        fac_combo["values"] = ["全部", "汽车人 (autobot)", "霸天虎 (decepticon)", "巨无霸 (maximal)", "原始兽 (predacon)"]
        fac_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0))
        fac_combo.bind("<<ComboboxSelected>>", self._on_search_changed)

        # Listbox with Scrollbar
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.bot_listbox = tk.Listbox(list_frame, font=("Segoe UI", 10), selectmode=tk.SINGLE, exportselection=False)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.bot_listbox.yview)
        self.bot_listbox.config(yscrollcommand=scrollbar.set)
        self.bot_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.bot_listbox.bind("<<ListboxSelect>>", self._on_bot_selected)

        # Bot count badge
        self.lbl_count = ttk.Label(left_frame, text="共 78 位英雄", anchor="center")
        self.lbl_count.pack(fill=tk.X, pady=2)

        # =====================================================================
        # RIGHT PANEL: Character Abilities Editor
        # =====================================================================
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)

        # Header bar (Bot Title & Meta & Live Preview Button)
        self.header_frame = ttk.LabelFrame(right_frame, text="当前选中机体", padding=8)
        self.header_frame.pack(fill=tk.X, padx=4, pady=2)

        self.lbl_bot_title = ttk.Label(self.header_frame, text="请从左侧选择一名变形金刚", font=("Microsoft YaHei", 13, "bold"))
        self.lbl_bot_title.pack(side=tk.LEFT, padx=4)

        self.lbl_bot_meta = ttk.Label(self.header_frame, text="", font=("Segoe UI", 10), foreground="#666666")
        self.lbl_bot_meta.pack(side=tk.LEFT, padx=12)

        # Prominent Live Preview Button in Header!
        btn_preview = ttk.Button(self.header_frame, text="👁️ 游戏内界面实时模拟预览 (Preview)", command=self._open_in_game_preview)
        btn_preview.pack(side=tk.RIGHT, padx=6)

        # Notebook tabs
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Tab 1: Special Attacks (Overhauled Multi-Effects Support!)
        self.tab_specials = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(self.tab_specials, text="特殊攻击 (SP1~SP3 多重效果)")
        self._build_specials_tab(self.tab_specials)

        # Tab 2: Signature Ability
        self.tab_signature = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.tab_signature, text="招牌能力 (Signature)")
        self._build_signature_tab(self.tab_signature)

        # Tab 3: Abilities Table (Passives / Basics)
        self.tab_abilities = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.tab_abilities, text="机体能力列表 (Abilities)")
        self._build_abilities_tab(self.tab_abilities)

        # Tab 4: Synergies
        self.tab_synergies = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.tab_synergies, text="协同奖励 (Synergies)")
        self._build_synergies_tab(self.tab_synergies)

        # Bottom Action Bar
        bottom_bar = ttk.Frame(right_frame, padding=6)
        bottom_bar.pack(fill=tk.X, padx=4, pady=4)

        btn_save = ttk.Button(bottom_bar, text="💾 保存当前英雄 (Save)", command=self._save_current_bot)
        btn_save.pack(side=tk.LEFT, padx=4)

        btn_preview2 = ttk.Button(bottom_bar, text="👁️ 实时预览 (Ctrl+P)", command=self._open_in_game_preview)
        btn_preview2.pack(side=tk.LEFT, padx=4)

        btn_gen = ttk.Button(bottom_bar, text="⚡ 生成离线游戏数据 (gamedata.py)", command=self._run_gamedata)
        btn_gen.pack(side=tk.LEFT, padx=4)

        btn_pull = ttk.Button(bottom_bar, text="☁️ 从 Upstash 云端同步此角色", command=self._pull_from_upstash)
        btn_pull.pack(side=tk.LEFT, padx=4)

        self.lbl_status = ttk.Label(bottom_bar, text="就绪", foreground="#008800")
        self.lbl_status.pack(side=tk.RIGHT, padx=6)

    # -------------------------------------------------------------------------
    # TAB 1: Special Attacks (SP1, SP2, SP3 with Multi-Effects Treeview)
    # -------------------------------------------------------------------------
    def _build_specials_tab(self, parent):
        self.sp_notebook = ttk.Notebook(parent)
        self.sp_notebook.pack(fill=tk.BOTH, expand=True)

        for idx in (1, 2, 3):
            tab = ttk.Frame(self.sp_notebook, padding=6)
            self.sp_notebook.add(tab, text=f"特殊技 {idx} (SP{idx})")
            self._build_single_sp_panel(tab, idx)

    def _build_single_sp_panel(self, parent, sp_idx):
        # 1. 招式官方名称
        f_top = ttk.LabelFrame(parent, text=f"SP{sp_idx} 官方招式名称", padding=6)
        f_top.pack(fill=tk.X, pady=(0, 4))

        f_row = ttk.Frame(f_top)
        f_row.pack(fill=tk.X, pady=2)

        ttk.Label(f_row, text="中文名称:", width=10).pack(side=tk.LEFT)
        name_var = tk.StringVar()
        name_ent = ttk.Entry(f_row, textvariable=name_var, width=24)
        name_ent.pack(side=tk.LEFT, padx=4)

        ttk.Label(f_row, text="英文名称:", width=10).pack(side=tk.LEFT, padx=(12, 0))
        name_en_var = tk.StringVar()
        name_en_ent = ttk.Entry(f_row, textvariable=name_en_var, width=24)
        name_en_ent.pack(side=tk.LEFT, padx=4)

        ttk.Label(f_row, text="激活分类:", width=10).pack(side=tk.LEFT, padx=(12, 0))
        ttk.Label(f_row, text=f"onSpecial{sp_idx}Hit (特殊攻击{sp_idx}命中时)", foreground="#0066cc").pack(side=tk.LEFT, padx=4)

        setattr(self, f"sp{sp_idx}_name_var", name_var)
        setattr(self, f"sp{sp_idx}_name_en_var", name_en_var)

        # 2. 效果列表 (Treeview)
        f_tree = ttk.LabelFrame(parent, text=f"SP{sp_idx} 包含的效果列表 (可配置多重机制，如破甲、能量窃取、生命窃取等)", padding=6)
        f_tree.pack(fill=tk.BOTH, expand=True, pady=4)

        t_frame = ttk.Frame(f_tree)
        t_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("idx", "title", "title_en", "pua", "desc_preview")
        tree = ttk.Treeview(t_frame, columns=cols, show="headings", height=5)
        tree.heading("idx", text="#")
        tree.heading("title", text="效果标题 (中文)")
        tree.heading("title_en", text="效果标题 (英文)")
        tree.heading("pua", text="PUA图标")
        tree.heading("desc_preview", text="效果描述摘要")

        tree.column("idx", width=40, anchor="center")
        tree.column("title", width=140)
        tree.column("title_en", width=140)
        tree.column("pua", width=90, anchor="center")
        tree.column("desc_preview", width=480)

        scroll = ttk.Scrollbar(t_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        tree.bind("<<TreeviewSelect>>", lambda e, idx=sp_idx: self._on_sp_effect_selected(idx, e))
        setattr(self, f"sp{sp_idx}_tree", tree)

        # Toolbar under tree
        tb = ttk.Frame(f_tree)
        tb.pack(fill=tk.X, pady=(4, 0))
        ttk.Button(tb, text="➕ 添加效果", command=lambda idx=sp_idx: self._add_sp_effect(idx)).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb, text="➖ 删除选中效果", command=lambda idx=sp_idx: self._delete_sp_effect(idx)).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb, text="⬆️ 上移", command=lambda idx=sp_idx: self._move_sp_effect(idx, -1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb, text="⬇️ 下移", command=lambda idx=sp_idx: self._move_sp_effect(idx, 1)).pack(side=tk.LEFT, padx=2)

        # 3. 选中效果详细编辑区
        f_edit = ttk.LabelFrame(parent, text="当前选中效果详细编辑", padding=6)
        f_edit.pack(fill=tk.X, expand=False, pady=4)

        f_e_meta = ttk.Frame(f_edit)
        f_e_meta.pack(fill=tk.X, pady=2)

        ttk.Label(f_e_meta, text="效果中文名:").pack(side=tk.LEFT)
        eff_title_var = tk.StringVar()
        ttk.Entry(f_e_meta, textvariable=eff_title_var, width=18).pack(side=tk.LEFT, padx=4)

        ttk.Label(f_e_meta, text="效果英文名:").pack(side=tk.LEFT, padx=(10, 0))
        eff_title_en_var = tk.StringVar()
        ttk.Entry(f_e_meta, textvariable=eff_title_en_var, width=18).pack(side=tk.LEFT, padx=4)

        ttk.Label(f_e_meta, text="PUA图标:").pack(side=tk.LEFT, padx=(10, 0))
        eff_pua_var = tk.StringVar()
        ttk.Entry(f_e_meta, textvariable=eff_pua_var, width=10).pack(side=tk.LEFT, padx=4)

        ttk.Label(f_e_meta, text="(如 E503 / 0xe41f)", foreground="#666666").pack(side=tk.LEFT, padx=4)

        btn_apply = ttk.Button(f_e_meta, text="✔ 保存当前效果修改", command=lambda idx=sp_idx: self._apply_sp_effect_edit(idx))
        btn_apply.pack(side=tk.RIGHT, padx=4)

        f_e_desc = ttk.Frame(f_edit)
        f_e_desc.pack(fill=tk.BOTH, expand=True, pady=4)
        ttk.Label(f_e_desc, text="效果描述文本:").pack(side=tk.LEFT, anchor=tk.N)
        eff_desc_text = scrolledtext.ScrolledText(f_e_desc, height=4, font=("Segoe UI", 9), wrap=tk.WORD)
        eff_desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

        setattr(self, f"sp{sp_idx}_eff_title_var", eff_title_var)
        setattr(self, f"sp{sp_idx}_eff_title_en_var", eff_title_en_var)
        setattr(self, f"sp{sp_idx}_eff_pua_var", eff_pua_var)
        setattr(self, f"sp{sp_idx}_eff_desc_text", eff_desc_text)

    def _refresh_sp_effects_tree(self, sp_idx):
        tree = getattr(self, f"sp{sp_idx}_tree")
        tree.delete(*tree.get_children())
        effects = self.sp_effects[sp_idx]
        for i, eff in enumerate(effects, start=1):
            p_desc = (eff.get("desc_zh", "") or "").replace("\n", " ")[:60]
            tree.insert("", tk.END, values=(i, eff.get("title_zh", ""), eff.get("title_en", ""), eff.get("pua_icon", ""), p_desc))

        # Update Tab Title with Count
        self.sp_notebook.tab(sp_idx - 1, text=f"特殊技 {sp_idx} (SP{sp_idx}) - {len(effects)}个效果")

    def _on_sp_effect_selected(self, sp_idx, event):
        tree = getattr(self, f"sp{sp_idx}_tree")
        sel = tree.selection()
        if not sel:
            return
        idx = int(tree.item(sel[0])["values"][0]) - 1
        effects = self.sp_effects[sp_idx]
        if 0 <= idx < len(effects):
            eff = effects[idx]
            getattr(self, f"sp{sp_idx}_eff_title_var").set(eff.get("title_zh", ""))
            getattr(self, f"sp{sp_idx}_eff_title_en_var").set(eff.get("title_en", ""))
            getattr(self, f"sp{sp_idx}_eff_pua_var").set(eff.get("pua_icon", ""))
            txt = getattr(self, f"sp{sp_idx}_eff_desc_text")
            txt.delete("1.0", tk.END)
            txt.insert("1.0", eff.get("desc_zh", ""))

    def _apply_sp_effect_edit(self, sp_idx, silent=False):
        tree = getattr(self, f"sp{sp_idx}_tree")
        sel = tree.selection()
        if not sel:
            if not silent:
                messagebox.showinfo("提示", "请先在效果列表中选中需要修改的行。")
            return
        idx = int(tree.item(sel[0])["values"][0]) - 1
        effects = self.sp_effects[sp_idx]
        if 0 <= idx < len(effects):
            eff = effects[idx]
            eff["title_zh"] = getattr(self, f"sp{sp_idx}_eff_title_var").get().strip()
            eff["title_en"] = getattr(self, f"sp{sp_idx}_eff_title_en_var").get().strip()
            eff["pua_icon"] = getattr(self, f"sp{sp_idx}_eff_pua_var").get().strip()
            eff["desc_zh"] = getattr(self, f"sp{sp_idx}_eff_desc_text").get("1.0", tk.END).strip()

            self._refresh_sp_effects_tree(sp_idx)
            # Reselect
            children = tree.get_children()
            if 0 <= idx < len(children):
                tree.selection_set(children[idx])
            if not silent:
                self.lbl_status.config(text=f"✔ 已更新 SP{sp_idx} 效果: {eff['title_zh']}", foreground="#008800")

    def _add_sp_effect(self, sp_idx):
        sp_name = getattr(self, f"sp{sp_idx}_name_var").get().strip() or f"SP{sp_idx}"
        new_eff = {
            "title_zh": f"{sp_name} 效果",
            "title_en": "New Effect",
            "pua_icon": "",
            "desc_zh": "请输入效果描述说明..."
        }
        self.sp_effects[sp_idx].append(new_eff)
        self._refresh_sp_effects_tree(sp_idx)
        tree = getattr(self, f"sp{sp_idx}_tree")
        children = tree.get_children()
        if children:
            tree.selection_set(children[-1])
            self._on_sp_effect_selected(sp_idx, None)

    def _delete_sp_effect(self, sp_idx):
        tree = getattr(self, f"sp{sp_idx}_tree")
        sel = tree.selection()
        if not sel:
            return
        idx = int(tree.item(sel[0])["values"][0]) - 1
        effects = self.sp_effects[sp_idx]
        if 0 <= idx < len(effects):
            t = effects[idx].get("title_zh", "")
            if messagebox.askyesno("确认删除", f"确定要删除 SP{sp_idx} 效果 [{t}] 吗？"):
                effects.pop(idx)
                self._refresh_sp_effects_tree(sp_idx)

    def _move_sp_effect(self, sp_idx, delta):
        tree = getattr(self, f"sp{sp_idx}_tree")
        sel = tree.selection()
        if not sel:
            return
        idx = int(tree.item(sel[0])["values"][0]) - 1
        effects = self.sp_effects[sp_idx]
        new_idx = idx + delta
        if 0 <= new_idx < len(effects):
            effects[idx], effects[new_idx] = effects[new_idx], effects[idx]
            self._refresh_sp_effects_tree(sp_idx)
            children = tree.get_children()
            tree.selection_set(children[new_idx])

    # -------------------------------------------------------------------------
    # TAB 2: Signature Ability
    # -------------------------------------------------------------------------
    def _build_signature_tab(self, parent):
        f_top = ttk.Frame(parent)
        f_top.pack(fill=tk.X, pady=4)

        ttk.Label(f_top, text="觉醒技名称:", width=12).pack(side=tk.LEFT)
        self.sig_title_var = tk.StringVar()
        ttk.Entry(f_top, textvariable=self.sig_title_var, width=26).pack(side=tk.LEFT, padx=4)

        ttk.Label(f_top, text="英文名称:", width=10).pack(side=tk.LEFT, padx=(12, 0))
        self.sig_title_en_var = tk.StringVar()
        ttk.Entry(f_top, textvariable=self.sig_title_en_var, width=26).pack(side=tk.LEFT, padx=4)

        ttk.Label(f_top, text="PUA 图标:").pack(side=tk.LEFT, padx=(12, 0))
        self.sig_pua_var = tk.StringVar()
        ttk.Entry(f_top, textvariable=self.sig_pua_var, width=10).pack(side=tk.LEFT, padx=4)

        f_tr = ttk.Frame(parent)
        f_tr.pack(fill=tk.X, pady=4)
        ttk.Label(f_tr, text="激活类别:", width=12).pack(side=tk.LEFT)
        self.sig_trigger_var = tk.StringVar(value="被动 (Passive)")
        sig_tr_combo = ttk.Combobox(f_tr, textvariable=self.sig_trigger_var, values=[opt[0] for opt in TRIGGER_OPTIONS], state="readonly", width=24)
        sig_tr_combo.pack(side=tk.LEFT, padx=4)
        ttk.Label(f_tr, text="(推荐保持为'被动', 客户端可精准命中官方汉化)", foreground="#666666").pack(side=tk.LEFT, padx=8)

        f_desc = ttk.LabelFrame(parent, text="觉醒技官方描述 (Signature Description)", padding=8)
        f_desc.pack(fill=tk.BOTH, expand=True, pady=6)
        self.sig_desc_text = scrolledtext.ScrolledText(f_desc, font=("Segoe UI", 10), wrap=tk.WORD)
        self.sig_desc_text.pack(fill=tk.BOTH, expand=True)

    # -------------------------------------------------------------------------
    # TAB 3: Abilities Table (Dual-Track, Custom Triggers Supported!)
    # -------------------------------------------------------------------------
    def _build_abilities_tab(self, parent):
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        cols = ("idx", "title", "trigger", "pua", "show_main", "desc_preview")
        self.ab_tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=6)
        self.ab_tree.heading("idx", text="#")
        self.ab_tree.heading("title", text="能力名称")
        self.ab_tree.heading("trigger", text="所属分类节 (Trigger)")
        self.ab_tree.heading("pua", text="PUA图标")
        self.ab_tree.heading("show_main", text="主界面显示")
        self.ab_tree.heading("desc_preview", text="描述摘要")

        self.ab_tree.column("idx", width=40, anchor="center")
        self.ab_tree.column("title", width=140)
        self.ab_tree.column("trigger", width=160)
        self.ab_tree.column("pua", width=80, anchor="center")
        self.ab_tree.column("show_main", width=90, anchor="center")
        self.ab_tree.column("desc_preview", width=420)

        ab_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.ab_tree.yview)
        self.ab_tree.configure(yscrollcommand=ab_scroll.set)
        self.ab_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ab_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.ab_tree.bind("<<TreeviewSelect>>", self._on_ability_row_selected)

        # Toolbar under table
        btn_row = ttk.Frame(parent)
        btn_row.pack(fill=tk.X, pady=4)
        ttk.Button(btn_row, text="➕ 新增能力", command=self._add_ability_row).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="➖ 删除选中能力", command=self._delete_ability_row).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="⬆️ 上移", command=lambda: self._move_ability(-1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="⬇️ 下移", command=lambda: self._move_ability(1)).pack(side=tk.LEFT, padx=2)

        # Edit frame for currently selected ability
        self.ab_edit_frame = ttk.LabelFrame(parent, text="编辑当前能力项", padding=6)
        self.ab_edit_frame.pack(fill=tk.BOTH, expand=False, pady=4)

        f_meta = ttk.Frame(self.ab_edit_frame)
        f_meta.pack(fill=tk.X, pady=2)
        ttk.Label(f_meta, text="能力标题:").pack(side=tk.LEFT)
        self.cur_ab_title_var = tk.StringVar()
        ttk.Entry(f_meta, textvariable=self.cur_ab_title_var, width=18).pack(side=tk.LEFT, padx=4)

        ttk.Label(f_meta, text="触发分类 (Trigger):").pack(side=tk.LEFT, padx=(8, 0))
        self.cur_ab_tr_var = tk.StringVar()
        # Custom typing allowed!
        ab_tr_combo = ttk.Combobox(f_meta, textvariable=self.cur_ab_tr_var, values=[opt[0] for opt in TRIGGER_OPTIONS], state="normal", width=20)
        ab_tr_combo.pack(side=tk.LEFT, padx=4)

        ttk.Label(f_meta, text="PUA图标:").pack(side=tk.LEFT, padx=(8, 0))
        self.cur_ab_pua_var = tk.StringVar()
        ttk.Entry(f_meta, textvariable=self.cur_ab_pua_var, width=8).pack(side=tk.LEFT, padx=4)

        self.cur_ab_show_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f_meta, text="主界面卡片显示 (Show on Main)", variable=self.cur_ab_show_var).pack(side=tk.LEFT, padx=8)

        f_desc = ttk.Frame(self.ab_edit_frame)
        f_desc.pack(fill=tk.BOTH, expand=True, pady=4)
        ttk.Label(f_desc, text="描述文本:").pack(side=tk.LEFT, anchor=tk.N)
        self.cur_ab_desc_text = scrolledtext.ScrolledText(f_desc, height=4, font=("Segoe UI", 9), wrap=tk.WORD)
        self.cur_ab_desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

        f_apply_row = ttk.Frame(self.ab_edit_frame)
        f_apply_row.pack(fill=tk.X, pady=2)
        ttk.Label(f_apply_row, text="提示: 触发分类支持手动输入任意自定义节标题，如'暴君重拳'、'减益控制'、'恐惧'等", foreground="#666666").pack(side=tk.LEFT)
        btn_apply_row = ttk.Button(f_apply_row, text="✔ 应用至列表 (Apply Row)", command=self._apply_current_ability_edit)
        btn_apply_row.pack(side=tk.RIGHT)

    # -------------------------------------------------------------------------
    # TAB 4: Synergies
    # -------------------------------------------------------------------------
    def _build_synergies_tab(self, parent):
        lbl = ttk.Label(parent, text="当前机体协同奖励列表 (只读/展示)", font=("Segoe UI", 10, "bold"))
        lbl.pack(anchor=tk.W, pady=4)

        cols = ("idx", "title", "heroes", "desc")
        self.syn_tree = ttk.Treeview(parent, columns=cols, show="headings", height=10)
        self.syn_tree.heading("idx", text="#")
        self.syn_tree.heading("title", text="协同名称")
        self.syn_tree.heading("heroes", text="协同金刚 ID")
        self.syn_tree.heading("desc", text="效果描述")

        self.syn_tree.column("idx", width=40, anchor="center")
        self.syn_tree.column("title", width=180)
        self.syn_tree.column("heroes", width=220)
        self.syn_tree.column("desc", width=480)

        self.syn_tree.pack(fill=tk.BOTH, expand=True, pady=4)

    def _populate_bot_list(self):
        self.bot_listbox.delete(0, tk.END)
        for b in self.filtered_bots:
            fac = "汽车人" if b["faction"] == "autobot" else ("霸天虎" if b["faction"] == "decepticon" else b["faction"])
            display_str = f"[{fac}] {b['name_zh']} ({b['bot_id']})"
            self.bot_listbox.insert(tk.END, display_str)

        self.lbl_count.config(text=f"已筛选 {len(self.filtered_bots)} / 共 {len(self.all_bots)} 位英雄")
        if self.filtered_bots:
            self.bot_listbox.selection_set(0)
            self._load_bot_by_index(0)

    def _on_search_changed(self, *args):
        kw = self.search_var.get().strip().lower()
        fac_choice = self.fac_var.get()

        fac_filter = ""
        if "autobot" in fac_choice or "汽车人" in fac_choice:
            fac_filter = "autobot"
        elif "decepticon" in fac_choice or "霸天虎" in fac_choice:
            fac_filter = "decepticon"
        elif "maximal" in fac_choice or "巨无霸" in fac_choice:
            fac_filter = "maximal"
        elif "predacon" in fac_choice or "原始兽" in fac_choice:
            fac_filter = "predacon"

        self.filtered_bots = [
            b for b in self.all_bots
            if (not kw or kw in b["name_zh"].lower() or kw in b["bot_id"].lower() or kw in b["name_en"].lower())
            and (not fac_filter or b["faction"] == fac_filter)
        ]
        self._populate_bot_list()

    def _on_bot_selected(self, event):
        sel = self.bot_listbox.curselection()
        if not sel:
            return
        self._load_bot_by_index(sel[0])

    def _load_bot_by_index(self, idx):
        if idx < 0 or idx >= len(self.filtered_bots):
            return
        bot_meta = self.filtered_bots[idx]
        self.current_bot_id = bot_meta["bot_id"]
        json_path = bot_meta["path"]

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                self.current_bot_data = json.load(f)
        except Exception as e:
            messagebox.showerror("读取错误", f"无法打开 {json_path}: {e}")
            return

        # Update Header
        name_zh = self.current_bot_data.get("name_zh", "")
        name_en = self.current_bot_data.get("name_en", "")
        bid = self.current_bot_data.get("bot_id", "")
        faction = self.current_bot_data.get("faction", "")
        bot_class = self.current_bot_data.get("class", "")
        self.lbl_bot_title.config(text=f"{name_zh} · {name_en}")
        self.lbl_bot_meta.config(text=f"ID: {bid} | 阵营: {faction} | 职业: {bot_class}")

        # Tab 1: Special Attacks with Multi-Effects
        specials = self.current_bot_data.get("special_attacks", {})
        for sp_idx in (1, 2, 3):
            cat = f"sp{sp_idx}"
            sp = specials.get(cat, {})
            getattr(self, f"sp{sp_idx}_name_var").set(sp.get("name_zh", ""))
            getattr(self, f"sp{sp_idx}_name_en_var").set(sp.get("name_en", ""))

            effects = sp.get("effects", [])
            if not effects:
                single_desc = sp.get("desc_zh", "")
                if single_desc:
                    effects = [{
                        "title_zh": sp.get("name_zh", f"SP{sp_idx} 效果"),
                        "title_en": sp.get("name_en", ""),
                        "pua_icon": sp.get("pua_icon", ""),
                        "desc_zh": single_desc
                    }]
                else:
                    effects = []

            self.sp_effects[sp_idx] = [dict(e) for e in effects]
            self._refresh_sp_effects_tree(sp_idx)

            # Auto-select first effect if exists
            tree = getattr(self, f"sp{sp_idx}_tree")
            children = tree.get_children()
            if children:
                tree.selection_set(children[0])
                self._on_sp_effect_selected(sp_idx, None)
            else:
                getattr(self, f"sp{sp_idx}_eff_title_var").set("")
                getattr(self, f"sp{sp_idx}_eff_title_en_var").set("")
                getattr(self, f"sp{sp_idx}_eff_pua_var").set("")
                getattr(self, f"sp{sp_idx}_eff_desc_text").delete("1.0", tk.END)

        # Tab 2: Signature
        sig = self.current_bot_data.get("signature", {})
        self.sig_title_var.set(sig.get("title_zh", ""))
        self.sig_title_en_var.set(sig.get("title_en", ""))
        self.sig_pua_var.set(sig.get("pua_icon", ""))
        tr_code = sig.get("ui_trigger", "none")
        self.sig_trigger_var.set(TRIGGER_LABEL_MAP.get(tr_code, "被动 (Passive)"))
        self.sig_desc_text.delete("1.0", tk.END)
        self.sig_desc_text.insert("1.0", sig.get("desc_zh", ""))

        # Tab 3: Abilities Treeview
        if "basic_abilities" in self.current_bot_data or "game_abilities" in self.current_bot_data:
            self.is_dual_track = True
            norm_abs = []
            for b in self.current_bot_data.get("basic_abilities", []):
                norm_abs.append({
                    "title_zh": b.get("title_zh", ""),
                    "title_en": b.get("title_en", ""),
                    "desc_zh": b.get("desc_zh", ""),
                    "pua_icon": b.get("pua_icon", ""),
                    "category": "basic",
                    "ui_trigger": "none",
                    "show_on_main_screen": True
                })
            for g in self.current_bot_data.get("game_abilities", []):
                norm_abs.append({
                    "title_zh": g.get("title_zh", ""),
                    "title_en": g.get("title_en", ""),
                    "desc_zh": g.get("desc_zh", ""),
                    "pua_icon": g.get("pua_icon", ""),
                    "category": "passive",
                    "ui_trigger": g.get("ui_trigger") or g.get("title_zh", "none"),
                    "show_on_main_screen": False
                })
            self.current_bot_data["abilities"] = norm_abs
        else:
            self.is_dual_track = False

        self._refresh_abilities_tree()

        # Tab 4: Synergies
        self.syn_tree.delete(*self.syn_tree.get_children())
        for syn_i, syn in enumerate(self.current_bot_data.get("synergies", []), start=1):
            h_str = ", ".join(syn.get("bonus_heroes", []))
            self.syn_tree.insert("", tk.END, values=(syn_i, syn.get("title_zh", ""), h_str, syn.get("desc_zh", "")))

        self.lbl_status.config(text=f"已加载: {name_zh} ({self.current_bot_id})", foreground="#0066cc")

    def _refresh_abilities_tree(self):
        self.ab_tree.delete(*self.ab_tree.get_children())
        abilities = self.current_bot_data.get("abilities", [])
        for i, ab in enumerate(abilities, start=1):
            tr_code = ab.get("ui_trigger", "none")
            tr_label = TRIGGER_LABEL_MAP.get(tr_code, tr_code)
            show_main = "✔ 是" if ab.get("show_on_main_screen", True) else "✖ 否"
            preview = (ab.get("desc_zh", "") or "").replace("\n", " ")[:60]
            self.ab_tree.insert("", tk.END, values=(i, ab.get("title_zh", ""), tr_label, ab.get("pua_icon", ""), show_main, preview))

    def _on_ability_row_selected(self, event):
        sel = self.ab_tree.selection()
        if not sel:
            return
        item = self.ab_tree.item(sel[0])
        idx = int(item["values"][0]) - 1
        abilities = self.current_bot_data.get("abilities", [])
        if 0 <= idx < len(abilities):
            ab = abilities[idx]
            self.cur_ab_title_var.set(ab.get("title_zh", ""))
            tr_code = ab.get("ui_trigger", "none")
            if tr_code in TRIGGER_LABEL_MAP:
                self.cur_ab_tr_var.set(TRIGGER_LABEL_MAP[tr_code])
            else:
                self.cur_ab_tr_var.set(tr_code)
            self.cur_ab_pua_var.set(ab.get("pua_icon", ""))
            self.cur_ab_show_var.set(bool(ab.get("show_on_main_screen", True)))
            self.cur_ab_desc_text.delete("1.0", tk.END)
            self.cur_ab_desc_text.insert("1.0", ab.get("desc_zh", ""))

    def _apply_current_ability_edit(self, silent=False):
        sel = self.ab_tree.selection()
        if not sel:
            if not silent:
                messagebox.showinfo("提示", "请先在上方表格中选中需要修改的能力行。")
            return
        idx = int(self.ab_tree.item(sel[0])["values"][0]) - 1
        abilities = self.current_bot_data.get("abilities", [])
        if 0 <= idx < len(abilities):
            ab = abilities[idx]
            ab["title_zh"] = self.cur_ab_title_var.get().strip()
            tr_label = self.cur_ab_tr_var.get().strip()
            if tr_label in TRIGGER_CODE_MAP:
                ab["ui_trigger"] = TRIGGER_CODE_MAP[tr_label]
            elif tr_label:
                ab["ui_trigger"] = tr_label
            else:
                ab["ui_trigger"] = "none"

            ab["pua_icon"] = self.cur_ab_pua_var.get().strip()
            ab["show_on_main_screen"] = self.cur_ab_show_var.get()
            ab["desc_zh"] = self.cur_ab_desc_text.get("1.0", tk.END).strip()

            self._refresh_abilities_tree()
            children = self.ab_tree.get_children()
            if 0 <= idx < len(children):
                self.ab_tree.selection_set(children[idx])
            if not silent:
                self.lbl_status.config(text=f"✔ 已更新能力: {ab['title_zh']}", foreground="#008800")

    def _add_ability_row(self):
        if not self.current_bot_data:
            return
        if "abilities" not in self.current_bot_data:
            self.current_bot_data["abilities"] = []
        new_ab = {
            "title_zh": "新能力",
            "title_en": "New Ability",
            "desc_zh": "请输入能力效果说明...",
            "pua_icon": "",
            "category": "passive",
            "ui_trigger": "none",
            "show_on_main_screen": False
        }
        self.current_bot_data["abilities"].append(new_ab)
        self._refresh_abilities_tree()
        children = self.ab_tree.get_children()
        if children:
            self.ab_tree.selection_set(children[-1])
            self._on_ability_row_selected(None)

    def _delete_ability_row(self):
        sel = self.ab_tree.selection()
        if not sel:
            return
        idx = int(self.ab_tree.item(sel[0])["values"][0]) - 1
        abilities = self.current_bot_data.get("abilities", [])
        if 0 <= idx < len(abilities):
            t = abilities[idx].get("title_zh", "")
            if messagebox.askyesno("确认删除", f"确定要删除能力 [{t}] 吗？"):
                abilities.pop(idx)
                self._refresh_abilities_tree()

    def _move_ability(self, delta):
        sel = self.ab_tree.selection()
        if not sel:
            return
        idx = int(self.ab_tree.item(sel[0])["values"][0]) - 1
        abilities = self.current_bot_data.get("abilities", [])
        new_idx = idx + delta
        if 0 <= new_idx < len(abilities):
            abilities[idx], abilities[new_idx] = abilities[new_idx], abilities[idx]
            self._refresh_abilities_tree()
            children = self.ab_tree.get_children()
            self.ab_tree.selection_set(children[new_idx])

    # -------------------------------------------------------------------------
    # Open In-Game Preview Modal
    # -------------------------------------------------------------------------
    def _open_in_game_preview(self):
        if not self.current_bot_data or not self.current_bot_id:
            messagebox.showinfo("提示", "请先从左侧列表选择一名变形金刚！")
            return

        # 1. Commit active edits in memory first so preview is 100% up to date
        for sp_idx in (1, 2, 3):
            self._apply_sp_effect_edit(sp_idx, silent=True)
            sp = self.current_bot_data.setdefault("special_attacks", {}).setdefault(f"sp{sp_idx}", {})
            sp["name_zh"] = getattr(self, f"sp{sp_idx}_name_var").get().strip()
            sp["name_en"] = getattr(self, f"sp{sp_idx}_name_en_var").get().strip()
            sp["effects"] = [dict(e) for e in self.sp_effects[sp_idx]]
            if self.sp_effects[sp_idx]:
                sp["desc_zh"] = self.sp_effects[sp_idx][0].get("desc_zh", "")
                sp["pua_icon"] = self.sp_effects[sp_idx][0].get("pua_icon", "")

        self._apply_current_ability_edit(silent=True)

        basic_list = []
        game_list = []
        for ab in self.current_bot_data.get("abilities", []):
            if ab.get("show_on_main_screen", False) or ab.get("category") == "basic":
                basic_list.append(dict(ab))
            else:
                game_list.append(dict(ab))
        self.current_bot_data["basic_abilities"] = basic_list
        self.current_bot_data["game_abilities"] = game_list

        sig = self.current_bot_data.setdefault("signature", {})
        sig["title_zh"] = self.sig_title_var.get().strip()
        sig["title_en"] = self.sig_title_en_var.get().strip()
        sig["pua_icon"] = self.sig_pua_var.get().strip()
        tr_label = self.sig_trigger_var.get()
        sig["ui_trigger"] = TRIGGER_CODE_MAP.get(tr_label, "none")
        sig["desc_zh"] = self.sig_desc_text.get("1.0", tk.END).strip()

        # Pop up preview window!
        InGamePreviewWindow(self, self.current_bot_data)

    # -------------------------------------------------------------------------
    # Save & Synchronize
    # -------------------------------------------------------------------------
    def _save_current_bot(self):
        if not self.current_bot_data or not self.current_bot_id:
            messagebox.showinfo("提示", "未选择任何英雄。")
            return

        # 1. Commit active edits
        for sp_idx in (1, 2, 3):
            self._apply_sp_effect_edit(sp_idx, silent=True)
        self._apply_current_ability_edit(silent=True)

        # 2. Collect Specials with Multi-Effects
        if "special_attacks" not in self.current_bot_data:
            self.current_bot_data["special_attacks"] = {}
        for i in (1, 2, 3):
            cat = f"sp{i}"
            if cat not in self.current_bot_data["special_attacks"]:
                self.current_bot_data["special_attacks"][cat] = {}
            sp = self.current_bot_data["special_attacks"][cat]
            sp["name_zh"] = getattr(self, f"sp{i}_name_var").get().strip()
            sp["name_en"] = getattr(self, f"sp{i}_name_en_var").get().strip()
            sp["effects"] = [dict(e) for e in self.sp_effects[i]]
            sp["ui_trigger"] = f"onSpecial{i}Hit"
            if self.sp_effects[i]:
                sp["desc_zh"] = self.sp_effects[i][0].get("desc_zh", "")
                sp["pua_icon"] = self.sp_effects[i][0].get("pua_icon", "")
            else:
                sp["desc_zh"] = ""
                sp["pua_icon"] = ""

        # 3. Collect Signature
        if "signature" not in self.current_bot_data:
            self.current_bot_data["signature"] = {}
        sig = self.current_bot_data["signature"]
        sig_title = self.sig_title_var.get().strip()
        sig_desc = self.sig_desc_text.get("1.0", tk.END).strip()
        if not sig_title:
            sig_title = "名称待定"
        if not sig_desc:
            sig_desc = "描述待定"
        sig["title_zh"] = sig_title
        sig["title_en"] = self.sig_title_en_var.get().strip() or "TBD"
        sig["pua_icon"] = self.sig_pua_var.get().strip()
        tr_label = self.sig_trigger_var.get()
        sig["ui_trigger"] = TRIGGER_CODE_MAP.get(tr_label, "none")
        sig["desc_zh"] = sig_desc

        # 4. Split abilities into basic_abilities and game_abilities
        basic_list = []
        game_list = []
        for ab in self.current_bot_data.get("abilities", []):
            if ab.get("show_on_main_screen", False) or ab.get("category") == "basic":
                basic_list.append({
                    "title_zh": ab.get("title_zh", "").strip(),
                    "title_en": ab.get("title_en", "").strip(),
                    "desc_zh": ab.get("desc_zh", "").strip(),
                    "pua_icon": ab.get("pua_icon", "").strip()
                })
            else:
                tr = ab.get("ui_trigger") or ab.get("title_zh") or "none"
                game_list.append({
                    "title_zh": ab.get("title_zh", "").strip(),
                    "title_en": ab.get("title_en", "").strip(),
                    "desc_zh": ab.get("desc_zh", "").strip(),
                    "pua_icon": ab.get("pua_icon", "").strip(),
                    "ui_trigger": tr.strip()
                })
        self.current_bot_data["basic_abilities"] = basic_list
        self.current_bot_data["game_abilities"] = game_list

        # 5. Save JSON
        json_path = CHAR_DATA_DIR / f"{self.current_bot_id}.json"
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(self.current_bot_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("保存失败", f"写入 JSON 失败: {e}")
            return

        # 6. Sync to SQLite DB
        self._sync_to_sqlite(self.current_bot_data)

        self.lbl_status.config(text=f"✔ 已保存至 {json_path.name} 与 SQLite", foreground="#008800")
        messagebox.showinfo("成功", f"英雄 [{self.current_bot_data.get('name_zh')}] 技能数据已成功保存！\n\n已更新:\n1. Server/character_data/{self.current_bot_id}.json\n2. Server/tftf_database.db")

    def _sync_to_sqlite(self, data):
        """同步更新 Server/tftf_database.db。"""
        if not DB_PATH.exists():
            return
        bid = data.get("bot_id")
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()

        try:
            # Update special attack names in characters table
            sp = data.get("special_attacks", {})
            sp1_z = sp.get("sp1", {}).get("name_zh", "")
            sp1_e = sp.get("sp1", {}).get("name_en", "")
            sp2_z = sp.get("sp2", {}).get("name_zh", "")
            sp2_e = sp.get("sp2", {}).get("name_en", "")
            sp3_z = sp.get("sp3", {}).get("name_zh", "")
            sp3_e = sp.get("sp3", {}).get("name_en", "")

            cur.execute(
                "UPDATE characters SET sp1_name_zh=?, sp1_name_en=?, sp2_name_zh=?, sp2_name_en=?, sp3_name_zh=?, sp3_name_en=? WHERE bot_id=?",
                (sp1_z, sp1_e, sp2_z, sp2_e, sp3_z, sp3_e, bid)
            )

            # Rebuild character_abilities for this bot
            cur.execute("DELETE FROM character_abilities WHERE bot_id=?", (bid,))

            # Signature
            sig = data.get("signature", {})
            if sig.get("title_zh") or sig.get("desc_zh"):
                cur.execute(
                    "INSERT INTO character_abilities (bot_id, category, title_zh, title_en, desc_zh, pua_icon, sort_order) VALUES (?, 'signature', ?, ?, ?, ?, 1)",
                    (bid, sig.get("title_zh", ""), sig.get("title_en", ""), sig.get("desc_zh", ""), sig.get("pua_icon", ""))
                )

            # Specials (supports multiple effects!)
            for i in (1, 2, 3):
                cat = f"sp{i}"
                sp_item = sp.get(cat, {})
                effects = sp_item.get("effects", [])
                if effects:
                    for eff_i, eff in enumerate(effects):
                        cur.execute(
                            f"INSERT INTO character_abilities (bot_id, category, title_zh, title_en, desc_zh, pua_icon, sort_order) VALUES (?, '{cat}', ?, ?, ?, ?, ?)",
                            (bid, eff.get("title_zh") or sp_item.get("name_zh", ""), eff.get("title_en") or sp_item.get("name_en", ""), eff.get("desc_zh", ""), eff.get("pua_icon", ""), i * 10 + eff_i)
                        )
                else:
                    cur.execute(
                        f"INSERT INTO character_abilities (bot_id, category, title_zh, title_en, desc_zh, pua_icon, sort_order) VALUES (?, '{cat}', ?, ?, ?, ?, ?)",
                        (bid, sp_item.get("name_zh", ""), sp_item.get("name_en", ""), sp_item.get("desc_zh", ""), sp_item.get("pua_icon", ""), i + 1)
                    )

            # Abilities (both basic and game)
            abs_list = []
            for b in data.get("basic_abilities", []):
                abs_list.append({"category": "basic", **b})
            for g in data.get("game_abilities", []):
                abs_list.append({"category": "passive", **g})
            if not abs_list:
                abs_list = data.get("abilities", [])

            for idx, ab in enumerate(abs_list, start=100):
                cur.execute(
                    "INSERT INTO character_abilities (bot_id, category, title_zh, title_en, desc_zh, pua_icon, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (bid, ab.get("category", "passive"), ab.get("title_zh", ""), ab.get("title_en", ""), ab.get("desc_zh", ""), ab.get("pua_icon", ""), idx)
                )

            # Synergies
            for idx, syn in enumerate(data.get("synergies", []), start=200):
                b_json = json.dumps(syn.get("bonus_heroes", []))
                cur.execute(
                    "INSERT INTO character_abilities (bot_id, category, title_zh, title_en, desc_zh, pua_icon, synergy_bots, sort_order) VALUES (?, 'synergy', ?, ?, ?, ?, ?, ?)",
                    (bid, syn.get("title_zh", ""), syn.get("title_en", ""), syn.get("desc_zh", ""), syn.get("pua_icon", ""), b_json, idx)
                )

            conn.commit()
        except Exception as e:
            print(f"Error syncing SQLite: {e}")
        finally:
            conn.close()

    def _run_gamedata(self):
        """执行 Server/gamedata.py 刷新全部离线数据。"""
        self.lbl_status.config(text="⏳ 正在重新生成游戏离线包 (gamedata.py)...", foreground="#cc6600")
        self.update()
        try:
            res = subprocess.run([sys.executable, "Server/gamedata.py"], cwd=ROOT_DIR, capture_output=True, text=True)
            if res.returncode == 0:
                self.lbl_status.config(text="✔ 离线数据包生成成功！", foreground="#008800")
                messagebox.showinfo("成功", "已成功重新生成全部离线响应包：\n- GET__bcg_getLoginData.json\n- GET__bcg_getUserData.json\n- bot_info.h")
            else:
                self.lbl_status.config(text="❌ gamedata.py 执行失败", foreground="#cc0000")
                messagebox.showerror("生成失败", res.stderr or res.stdout)
        except Exception as e:
            messagebox.showerror("异常", f"执行失败: {e}")

    def _pull_from_upstash(self):
        """从 Upstash KV 拉取指定角色最新数据。"""
        if not self.current_bot_id:
            return
        self.lbl_status.config(text=f"⏳ 正在从云端 Upstash 拉取 {self.current_bot_id}...", foreground="#cc6600")
        self.update()
        try:
            res = subprocess.run([sys.executable, "tools/sync_from_upstash.py", "--bot", self.current_bot_id], cwd=ROOT_DIR, capture_output=True, text=True)
            if res.returncode == 0:
                subprocess.run([sys.executable, "tools/export_all_character_data.py"], cwd=ROOT_DIR, capture_output=True)
                sel = self.bot_listbox.curselection()
                if sel:
                    self._load_bot_by_index(sel[0])
                self.lbl_status.config(text="✔ 云端拉取并同步成功！", foreground="#008800")
                messagebox.showinfo("成功", f"已成功从 Upstash KV 拉取 {self.current_bot_id} 并刷新本地！")
            else:
                self.lbl_status.config(text="❌ 云端拉取失败", foreground="#cc0000")
                messagebox.showerror("拉取失败", res.stderr or res.stdout)
        except Exception as e:
            messagebox.showerror("异常", f"拉取失败: {e}")


if __name__ == "__main__":
    app = AbilityStudioApp()
    app.mainloop()
