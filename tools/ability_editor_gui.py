#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TFTF 技能与能力可视化桌面编辑器 (Character Abilities Studio)
==========================================================
支持直观查看、修改 78 位英雄的：
1. 招牌能力 (名称、PUA图标、触发类别、技能描述)
2. 机体能力 (被动、重击、远程等触发节、PUA图标、主界面显示开关、说明文案)
3. 特殊攻击 1/2/3 (技能名称、说明文案、PUA图标)
4. 协同奖励与羁绊金刚

双向存储：实时更新 Server/character_data/{bot_id}.json 明文文件与 Server/tftf_database.db。
运行方式:
    python tools/ability_editor_gui.py
"""

import os
import sys
import json
import sqlite3
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path

# Force UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

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


class AbilityStudioApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TFTF 技能与能力可视化编辑器 — Character Abilities Studio")
        self.geometry("1150x780")
        self.minsize(980, 650)

        # Apply clean ttk style
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.all_bots = []
        self.filtered_bots = []
        self.current_bot_id = None
        self.current_bot_data = None

        self._load_all_bots_metadata()
        self._build_ui()
        self._populate_bot_list()

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

        # Header bar (Bot Title & Meta)
        self.header_frame = ttk.LabelFrame(right_frame, text="当前选中机体", padding=8)
        self.header_frame.pack(fill=tk.X, padx=4, pady=2)

        self.lbl_bot_title = ttk.Label(self.header_frame, text="请从左侧选择一名变形金刚", font=("Segoe UI", 13, "bold"))
        self.lbl_bot_title.pack(side=tk.LEFT, padx=4)

        self.lbl_bot_meta = ttk.Label(self.header_frame, text="", font=("Segoe UI", 10), foreground="#666666")
        self.lbl_bot_meta.pack(side=tk.LEFT, padx=12)

        # Notebook tabs
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Tab 1: Special Attacks
        self.tab_specials = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.tab_specials, text="特殊攻击 (SP1~SP3)")
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

        btn_gen = ttk.Button(bottom_bar, text="⚡ 生成离线游戏数据 (gamedata.py)", command=self._run_gamedata)
        btn_gen.pack(side=tk.LEFT, padx=4)

        btn_pull = ttk.Button(bottom_bar, text="☁️ 从 Upstash 云端同步此角色", command=self._pull_from_upstash)
        btn_pull.pack(side=tk.LEFT, padx=4)

        self.lbl_status = ttk.Label(bottom_bar, text="就绪", foreground="#008800")
        self.lbl_status.pack(side=tk.RIGHT, padx=6)

    def _build_specials_tab(self, parent):
        for idx in (1, 2, 3):
            group = ttk.LabelFrame(parent, text=f"特殊攻击 {idx} (Special Attack {idx})", padding=8)
            group.pack(fill=tk.X, expand=False, pady=4)

            f1 = ttk.Frame(group)
            f1.pack(fill=tk.X, pady=2)
            ttk.Label(f1, text="中文名称:", width=10).pack(side=tk.LEFT)
            name_var = tk.StringVar()
            name_ent = ttk.Entry(f1, textvariable=name_var, width=28)
            name_ent.pack(side=tk.LEFT, padx=4)

            ttk.Label(f1, text="英文名称:", width=10).pack(side=tk.LEFT, padx=(12, 0))
            name_en_var = tk.StringVar()
            name_en_ent = ttk.Entry(f1, textvariable=name_en_var, width=28)
            name_en_ent.pack(side=tk.LEFT, padx=4)

            ttk.Label(f1, text="PUA图标:").pack(side=tk.LEFT, padx=(12, 0))
            pua_var = tk.StringVar()
            pua_ent = ttk.Entry(f1, textvariable=pua_var, width=8)
            pua_ent.pack(side=tk.LEFT, padx=4)

            f2 = ttk.Frame(group)
            f2.pack(fill=tk.X, pady=4)
            ttk.Label(f2, text="技能描述:", width=10).pack(side=tk.LEFT, anchor=tk.N)
            desc_text = scrolledtext.ScrolledText(f2, height=3, font=("Segoe UI", 9), wrap=tk.WORD)
            desc_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

            setattr(self, f"sp{idx}_name_var", name_var)
            setattr(self, f"sp{idx}_name_en_var", name_en_var)
            setattr(self, f"sp{idx}_pua_var", pua_var)
            setattr(self, f"sp{idx}_desc_text", desc_text)

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

    def _build_abilities_tab(self, parent):
        # Top Table of abilities
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
        ttk.Entry(f_meta, textvariable=self.cur_ab_title_var, width=20).pack(side=tk.LEFT, padx=4)

        ttk.Label(f_meta, text="触发分类:").pack(side=tk.LEFT, padx=(8, 0))
        self.cur_ab_tr_var = tk.StringVar()
        ab_tr_combo = ttk.Combobox(f_meta, textvariable=self.cur_ab_tr_var, values=[opt[0] for opt in TRIGGER_OPTIONS], state="readonly", width=18)
        ab_tr_combo.pack(side=tk.LEFT, padx=4)

        ttk.Label(f_meta, text="PUA图标:").pack(side=tk.LEFT, padx=(8, 0))
        self.cur_ab_pua_var = tk.StringVar()
        ttk.Entry(f_meta, textvariable=self.cur_ab_pua_var, width=8).pack(side=tk.LEFT, padx=4)

        self.cur_ab_show_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f_meta, text="主界面显示 (Show on Main)", variable=self.cur_ab_show_var).pack(side=tk.LEFT, padx=8)

        f_desc = ttk.Frame(self.ab_edit_frame)
        f_desc.pack(fill=tk.BOTH, expand=True, pady=4)
        ttk.Label(f_desc, text="描述文本:").pack(side=tk.LEFT, anchor=tk.N)
        self.cur_ab_desc_text = scrolledtext.ScrolledText(f_desc, height=4, font=("Segoe UI", 9), wrap=tk.WORD)
        self.cur_ab_desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

        btn_apply_row = ttk.Button(self.ab_edit_frame, text="✔ 应用至列表 (Apply Row)", command=self._apply_current_ability_edit)
        btn_apply_row.pack(anchor=tk.E, pady=2)

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

        # Tab 1: Specials
        specials = self.current_bot_data.get("special_attacks", {})
        for i in (1, 2, 3):
            cat = f"sp{i}"
            sp = specials.get(cat, {})
            getattr(self, f"sp{i}_name_var").set(sp.get("name_zh", ""))
            getattr(self, f"sp{i}_name_en_var").set(sp.get("name_en", ""))
            getattr(self, f"sp{i}_pua_var").set(sp.get("pua_icon", ""))
            txt_box = getattr(self, f"sp{i}_desc_text")
            txt_box.delete("1.0", tk.END)
            txt_box.insert("1.0", sp.get("desc_zh", ""))

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
            self.cur_ab_tr_var.set(TRIGGER_LABEL_MAP.get(tr_code, "被动 (Passive)"))
            self.cur_ab_pua_var.set(ab.get("pua_icon", ""))
            self.cur_ab_show_var.set(bool(ab.get("show_on_main_screen", True)))
            self.cur_ab_desc_text.delete("1.0", tk.END)
            self.cur_ab_desc_text.insert("1.0", ab.get("desc_zh", ""))

    def _apply_current_ability_edit(self):
        sel = self.ab_tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先在上方表格中选中需要修改的能力行。")
            return
        idx = int(self.ab_tree.item(sel[0])["values"][0]) - 1
        abilities = self.current_bot_data.get("abilities", [])
        if 0 <= idx < len(abilities):
            ab = abilities[idx]
            ab["title_zh"] = self.cur_ab_title_var.get().strip()
            tr_label = self.cur_ab_tr_var.get()
            ab["ui_trigger"] = TRIGGER_CODE_MAP.get(tr_label, "none")
            ab["pua_icon"] = self.cur_ab_pua_var.get().strip()
            ab["show_on_main_screen"] = self.cur_ab_show_var.get()
            ab["desc_zh"] = self.cur_ab_desc_text.get("1.0", tk.END).strip()

            self._refresh_abilities_tree()
            self.lbl_status.config(text=f"已更新能力: {ab['title_zh']}", foreground="#008800")

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
            "show_on_main_screen": True
        }
        self.current_bot_data["abilities"].append(new_ab)
        self._refresh_abilities_tree()
        # select the last item
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

    def _save_current_bot(self):
        if not self.current_bot_data or not self.current_bot_id:
            messagebox.showinfo("提示", "未选择任何英雄。")
            return

        # 1. Collect Specials
        if "special_attacks" not in self.current_bot_data:
            self.current_bot_data["special_attacks"] = {}
        for i in (1, 2, 3):
            cat = f"sp{i}"
            if cat not in self.current_bot_data["special_attacks"]:
                self.current_bot_data["special_attacks"][cat] = {}
            sp = self.current_bot_data["special_attacks"][cat]
            sp["name_zh"] = getattr(self, f"sp{i}_name_var").get().strip()
            sp["name_en"] = getattr(self, f"sp{i}_name_en_var").get().strip()
            sp["pua_icon"] = getattr(self, f"sp{i}_pua_var").get().strip()
            sp["desc_zh"] = getattr(self, f"sp{i}_desc_text").get("1.0", tk.END).strip()
            sp["ui_trigger"] = f"onSpecial{i}Hit"

        # 2. Collect Signature
        if "signature" not in self.current_bot_data:
            self.current_bot_data["signature"] = {}
        sig = self.current_bot_data["signature"]
        sig["title_zh"] = self.sig_title_var.get().strip()
        sig["title_en"] = self.sig_title_en_var.get().strip()
        sig["pua_icon"] = self.sig_pua_var.get().strip()
        tr_label = self.sig_trigger_var.get()
        sig["ui_trigger"] = TRIGGER_CODE_MAP.get(tr_label, "none")
        sig["desc_zh"] = self.sig_desc_text.get("1.0", tk.END).strip()

        # 3. Save JSON
        json_path = CHAR_DATA_DIR / f"{self.current_bot_id}.json"
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(self.current_bot_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("保存失败", f"写入 JSON 失败: {e}")
            return

        # 4. Sync to SQLite DB (character_abilities and characters tables)
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

            # Specials
            for i in (1, 2, 3):
                cat = f"sp{i}"
                sp_item = sp.get(cat, {})
                cur.execute(
                    f"INSERT INTO character_abilities (bot_id, category, title_zh, title_en, desc_zh, pua_icon, sort_order) VALUES (?, '{cat}', ?, ?, ?, ?, ?)",
                    (bid, sp_item.get("name_zh", ""), sp_item.get("name_en", ""), sp_item.get("desc_zh", ""), sp_item.get("pua_icon", ""), i + 1)
                )

            # Abilities
            for idx, ab in enumerate(data.get("abilities", []), start=5):
                cur.execute(
                    "INSERT INTO character_abilities (bot_id, category, title_zh, title_en, desc_zh, pua_icon, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (bid, ab.get("category", "passive"), ab.get("title_zh", ""), ab.get("title_en", ""), ab.get("desc_zh", ""), ab.get("pua_icon", ""), idx)
                )

            # Synergies
            for idx, syn in enumerate(data.get("synergies", []), start=20):
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
                # Re-export json
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
