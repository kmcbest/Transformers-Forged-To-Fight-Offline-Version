#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transformers: Forged to Fight - Fandom Wiki 角色属性抓取 GUI 工具
- 支持多行 TextBox 粘贴角色名（一行一个，自动将空格替换为下划线）
- 自动多线程抓取 6/60 属性（绕过反爬验证，遇到抓不到的先跳过）
- 自动执行插值补全（基于 5/50 或已有角色基准编入 6/60）
- 默认增量合并保存到 JSON，绝不覆盖已有历史数据
"""

import sys
import os
import re
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# 5/50 到 6/60 的官方增幅拟合系数
GROWTH_HP_5TO6 = 1.1495
GROWTH_ATK_5TO6 = 1.1495
GROWTH_RATING_5TO6 = 1.3000

DEFAULT_JSON_PATH = Path(__file__).resolve().parent / "fandom_bot_stats.json"

DEFAULT_TEXT = """Grimlock
Grindor
Ironhide
Motormaster
Optimus Prime (MV1)
Sunstreaker"""

def clean_num(val):
    if val is None:
        return None
    val_str = str(val).strip()
    digits = re.sub(r"[^\d]", "", val_str)
    return int(digits) if digits else None

def fmt_num(val):
    if val is None:
        return "-"
    return f"{val:,}"

def fetch_fandom_page(page_name):
    wiki_title = page_name.strip().replace(" ", "_")
    api_url = "https://transformers-forged-to-fight.fandom.com/api.php"
    params = {
        "action": "parse",
        "page": wiki_title,
        "prop": "text|wikitext",
        "format": "json"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    resp = requests.get(api_url, params=params, headers=headers, timeout=12)
    data = resp.json()
    if "error" in data:
        raise ValueError(data["error"].get("info", "Fandom API Error"))
    
    html = data["parse"]["text"]["*"]
    wikitext = data["parse"].get("wikitext", {}).get("*", "")
    return html, wikitext

def parse_stats_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    rows_found = {}

    for table in soup.find_all("table"):
        tr_list = table.find_all("tr")
        if not tr_list:
            continue
        
        header_texts = []
        for r in tr_list[:2]:
            th_tds = [c.get_text(strip=True).lower() for c in r.find_all(["th", "td"])]
            if any("health" in h or "hp" in h for h in th_tds) and any("attack" in h or "atk" in h for h in th_tds):
                header_texts = th_tds
                break
        
        if not header_texts:
            continue
        
        col_rank = -1
        col_hp = -1
        col_atk = -1
        col_rat = -1
        for idx, h in enumerate(header_texts):
            h_clean = h.strip().lower()
            if ("rank" in h_clean or "level" in h_clean) and "sig" not in h_clean:
                if col_rank == -1:
                    col_rank = idx
            elif "health" in h_clean or "hp" in h_clean:
                col_hp = idx
            elif "attack" in h_clean or "atk" in h_clean:
                col_atk = idx
            elif "rating" in h_clean or "pi" in h_clean:
                col_rat = idx

        for r in tr_list:
            cells = [c.get_text(strip=True) for c in r.find_all(["th", "td"])]
            if not cells:
                continue
            
            rank_cell = cells[col_rank] if (col_rank >= 0 and col_rank < len(cells)) else cells[0]
            for target_rank in ["6/60", "5/50"]:
                if target_rank in rank_cell or (cells and cells[0] == target_rank):
                    hp_v = clean_num(cells[col_hp] if col_hp >= 0 and col_hp < len(cells) else (cells[1] if len(cells)>1 else None))
                    atk_v = clean_num(cells[col_atk] if col_atk >= 0 and col_atk < len(cells) else (cells[2] if len(cells)>2 else None))
                    rat_v = clean_num(cells[col_rat] if col_rat >= 0 and col_rat < len(cells) else (cells[3] if len(cells)>3 else None))
                    if hp_v and atk_v:
                        rows_found[target_rank] = (hp_v, atk_v, rat_v)

    return rows_found

def parse_stats_from_wikitext(wikitext):
    if not wikitext:
        return None
    m_sec = re.search(r"==\s*Max Stats\s*==([\s\S]*?)(==|\Z)", wikitext, re.IGNORECASE)
    if not m_sec:
        return None
    sec_text = m_sec.group(1)
    
    m_5star = re.search(r"\*+.*5-Star[\s\S]*?(?=\*+[1-4]-Star|\Z)", sec_text, re.IGNORECASE)
    target_block = m_5star.group(0) if m_5star else sec_text
    
    hp_m = re.search(r"Health\s*[:=]\s*([\d,.]+)", target_block, re.IGNORECASE)
    atk_m = re.search(r"Attack\s*[:=]\s*([\d,.]+)", target_block, re.IGNORECASE)
    rat_m = re.search(r"(?:Max\s*)?Rating\s*[:=]\s*([\d,.]+)", target_block, re.IGNORECASE)
    
    if hp_m and atk_m:
        return (clean_num(hp_m.group(1)), clean_num(atk_m.group(1)), clean_num(rat_m.group(1)) if rat_m else None)
    return None

def fetch_single_bot(bot_name):
    wiki_page = bot_name.strip().replace(" ", "_")
    try:
        html, wikitext = fetch_fandom_page(wiki_page)
    except Exception as e:
        return None

    table_stats = parse_stats_from_html(html)
    if "6/60" in table_stats:
        hp, atk, rat = table_stats["6/60"]
        return {
            "name": bot_name,
            "wiki_page": wiki_page,
            "rank_level": "6/60",
            "match_type": "exact",
            "health": hp,
            "attack": atk,
            "rating": rat,
        }
    if "5/50" in table_stats:
        hp, atk, rat = table_stats["5/50"]
        return {
            "name": bot_name,
            "wiki_page": wiki_page,
            "rank_level": "5/50",
            "match_type": "found_5_50",
            "health": hp,
            "attack": atk,
            "rating": rat,
        }

    wiki_stats = parse_stats_from_wikitext(wikitext)
    if wiki_stats:
        hp, atk, rat = wiki_stats
        return {
            "name": bot_name,
            "wiki_page": wiki_page,
            "rank_level": "6/60" if (hp and hp >= 33000) else "5/50",
            "match_type": "exact (wikitext)" if (hp and hp >= 33000) else "found_5_50_wikitext",
            "health": hp,
            "attack": atk,
            "rating": rat,
        }

    return None

class ScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TFTF Fandom 角色属性抓取器 (GUI)")
        self.root.geometry("980x720")
        self.root.minsize(800, 600)

        self.is_running = False
        self.stop_requested = False

        self._setup_style()
        self._build_ui()
        self._update_json_status()

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # 配色与按钮
        style.configure("TLabel", font=("Segoe UI", 9))
        style.configure("Title.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("TButton", font=("Segoe UI", 9), padding=5)
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), foreground="#ffffff", background="#007acc")
        style.map("Accent.TButton", background=[("active", "#005999"), ("disabled", "#cccccc")])
        
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=24)

    def _build_ui(self):
        # 顶部标题栏
        top_frame = ttk.Frame(self.root, padding=(12, 10, 12, 6))
        top_frame.pack(fill=tk.X)

        title_lbl = ttk.Label(top_frame, text="🤖 Transformers: Forged to Fight - Fandom 属性抓取器", style="Title.TLabel")
        title_lbl.pack(side=tk.LEFT)

        desc_lbl = ttk.Label(top_frame, text="（自动去除反爬限制 · 抓不到跳过 · 自动插值到 6/60 · 增量写入 JSON）", foreground="#666666")
        desc_lbl.pack(side=tk.LEFT, padx=10, pady=2)

        # 主工作区（左侧输入，右侧结果）
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        # 左侧面板：角色输入
        left_frame = ttk.LabelFrame(paned, text=" 角色名输入 (每行一个，可直接从剪贴板粘贴) ", padding=8)
        paned.add(left_frame, weight=1)

        self.txt_input = tk.Text(left_frame, wrap=tk.NONE, font=("Consolas", 10), width=32)
        self.txt_input.insert(tk.END, DEFAULT_TEXT)
        scroll_y = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.txt_input.yview)
        scroll_x = ttk.Scrollbar(left_frame, orient=tk.HORIZONTAL, command=self.txt_input.xview)
        self.txt_input.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.txt_input.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        # 输入快捷按钮区
        btn_box = ttk.Frame(left_frame, padding=(0, 6, 0, 0))
        btn_box.grid(row=2, column=0, columnspan=2, sticky="ew")

        ttk.Button(btn_box, text="清空输入", command=self._clear_input).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_box, text="载入示例", command=self._load_sample).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_box, text="全网拉取所有69位角色", command=self._fetch_all_wiki_bots).pack(side=tk.RIGHT, padx=2)

        # 右侧面板：抓取日志与结果表格
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        # 右侧结果表格
        table_frame = ttk.LabelFrame(right_frame, text=" 抓取与插值结果预览 (6/60) ", padding=6)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "rank", "hp", "atk", "rating", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="角色名")
        self.tree.heading("rank", text="等级")
        self.tree.heading("hp", text="Health (HP)")
        self.tree.heading("atk", text="Attack (ATK)")
        self.tree.heading("rating", text="Rating (战力)")
        self.tree.heading("status", text="数据来源 / 状态")

        self.tree.column("name", width=140, anchor="w")
        self.tree.column("rank", width=55, anchor="center")
        self.tree.column("hp", width=85, anchor="e")
        self.tree.column("atk", width=85, anchor="e")
        self.tree.column("rating", width=95, anchor="e")
        self.tree.column("status", width=160, anchor="w")

        tree_scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # 实时日志窗口
        log_frame = ttk.LabelFrame(right_frame, text=" 实时抓取日志 ", padding=6)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        self.txt_log = tk.Text(log_frame, wrap=tk.WORD, font=("Consolas", 9), height=7, bg="#1e1e1e", fg="#d4d4d4")
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=log_scroll.set)
        self.txt_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 底部配置与控制栏
        bottom_frame = ttk.Frame(self.root, padding=(12, 6, 12, 12))
        bottom_frame.pack(fill=tk.X)

        # 输出文件配置行
        file_row = ttk.Frame(bottom_frame)
        file_row.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(file_row, text="导出 JSON 路径:").pack(side=tk.LEFT)
        self.var_output = tk.StringVar(value=str(DEFAULT_JSON_PATH))
        self.ent_output = ttk.Entry(file_row, textvariable=self.var_output)
        self.ent_output.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(file_row, text="浏览...", command=self._browse_output).pack(side=tk.LEFT)

        self.var_incremental = tk.BooleanVar(value=True)
        chk_inc = ttk.Checkbutton(file_row, text="增量保存（保留原有数据，不覆盖）", variable=self.var_incremental)
        chk_inc.pack(side=tk.LEFT, padx=12)

        # 状态行与控制按钮
        ctrl_row = ttk.Frame(bottom_frame)
        ctrl_row.pack(fill=tk.X)

        self.prog_bar = ttk.Progressbar(ctrl_row, orient=tk.HORIZONTAL, mode="determinate")
        self.prog_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.lbl_status = ttk.Label(ctrl_row, text="就绪", foreground="#333333")
        self.lbl_status.pack(side=tk.LEFT, padx=(0, 15))

        self.btn_run = ttk.Button(ctrl_row, text="🚀 开始抓取", style="Accent.TButton", command=self._start_scraping)
        self.btn_run.pack(side=tk.RIGHT, padx=4)

        self.btn_stop = ttk.Button(ctrl_row, text="停止", state=tk.DISABLED, command=self._stop_scraping)
        self.btn_stop.pack(side=tk.RIGHT)

        ttk.Button(ctrl_row, text="📂 打开 JSON 文件", command=self._open_json_file).pack(side=tk.RIGHT, padx=4)

    def _log(self, msg):
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)

    def _clear_input(self):
        self.txt_input.delete("1.0", tk.END)

    def _load_sample(self):
        self.txt_input.delete("1.0", tk.END)
        self.txt_input.insert(tk.END, DEFAULT_TEXT)

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            title="选择导出 JSON 文件",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialdir=str(DEFAULT_JSON_PATH.parent),
            initialfile=DEFAULT_JSON_PATH.name
        )
        if path:
            self.var_output.set(path)
            self._update_json_status()

    def _update_json_status(self):
        p = Path(self.var_output.get())
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                self.lbl_status.config(text=f"目标 JSON 已有 {len(data)} 个角色记录")
            except Exception:
                self.lbl_status.config(text="目标 JSON 文件已存在")
        else:
            self.lbl_status.config(text="目标 JSON 尚未创建")

    def _open_json_file(self):
        p = Path(self.var_output.get())
        if p.exists():
            if sys.platform == "win32":
                os.startfile(str(p))
            else:
                import subprocess
                subprocess.run(["xdg-open", str(p)])
        else:
            messagebox.showwarning("提示", f"JSON 文件尚未生成: {p}")

    def _fetch_all_wiki_bots(self):
        def worker():
            self._log("[*] 正在从 Wiki /Bots 页面获取全部官方角色名单...")
            try:
                html, _ = fetch_fandom_page("Bots")
                soup = BeautifulSoup(html, "html.parser")
                bot_names = []
                for div in soup.find_all("div", class_="gallery-image-wrapper"):
                    a = div.find("a")
                    if a and a.get("href"):
                        wiki_page = a.get("href").replace("/wiki/", "").strip()
                        wiki_page = wiki_page.replace("_", " ")
                        if wiki_page and wiki_page not in bot_names:
                            bot_names.append(wiki_page)
                self.root.after(0, lambda: self._apply_all_bots(bot_names))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"[-] 获取全量角色名单失败: {e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_all_bots(self, bot_names):
        self.txt_input.delete("1.0", tk.END)
        self.txt_input.insert(tk.END, "\n".join(bot_names))
        self._log(f"[+] 成功载入全部 {len(bot_names)} 位官方角色名单！可以直接点击“开始抓取”！")

    def _start_scraping(self):
        raw_text = self.txt_input.get("1.0", tk.END)
        lines = [line.strip() for line in raw_text.splitlines() if line.strip() and not line.strip().startswith("#")]
        if not lines:
            messagebox.showwarning("提示", "请输入或粘贴至少一个角色名字！")
            return

        self.is_running = True
        self.stop_requested = False
        self.btn_run.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.txt_input.config(state=tk.DISABLED)
        
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.prog_bar["maximum"] = len(lines)
        self.prog_bar["value"] = 0

        out_path = Path(self.var_output.get())
        is_incremental = self.var_incremental.get()

        self._log(f"=== 开始抓取任务 (总计 {len(lines)} 个角色) ===")
        threading.Thread(target=self._scrape_worker, args=(lines, out_path, is_incremental), daemon=True).start()

    def _stop_scraping(self):
        if self.is_running:
            self.stop_requested = True
            self._log("[!] 正在中止抓取...")

    def _scrape_worker(self, bot_list, out_path, is_incremental):
        # 1. 读取既有数据 (增量模式)
        existing_data = {}
        if is_incremental and out_path.exists():
            try:
                existing_data = json.loads(out_path.read_text(encoding="utf-8"))
                self.root.after(0, lambda: self._log(f"[*] 增量模式: 已载入先前 {len(existing_data)} 条已有角色数据"))
            except Exception:
                existing_data = {}

        raw_results = {}
        exact_660_list = []

        # 2. 依次抓取
        for idx, bot_name in enumerate(bot_list, 1):
            if self.stop_requested:
                self.root.after(0, lambda: self._log("[!] 抓取已被用户手动中止！"))
                break

            wiki_page = bot_name.strip().replace(" ", "_")
            self.root.after(0, lambda i=idx, n=bot_name: self.lbl_status.config(text=f"正在抓取 ({i}/{len(bot_list)}): {n}..."))

            res = fetch_single_bot(bot_name)
            raw_results[bot_name] = res

            if res and res["rank_level"] == "6/60":
                exact_660_list.append(res)
                log_msg = f"[{idx}/{len(bot_list)}] ✔ [已抓取 6/60] {bot_name:<20} | HP: {fmt_num(res['health']):>7} | ATK: {fmt_num(res['attack']):>6} | Rating: {fmt_num(res['rating']):>7}"
                row_data = (bot_name, "6/60", fmt_num(res["health"]), fmt_num(res["attack"]), fmt_num(res["rating"]), "✔ 原版 6/60")
            elif res and res["rank_level"] == "5/50":
                log_msg = f"[{idx}/{len(bot_list)}] ✔ [抓到 5/50]   {bot_name:<20} | HP: {fmt_num(res['health']):>7} | ATK: {fmt_num(res['attack']):>6} (将在最后插值到6/60)"
                row_data = (bot_name, "5/50", fmt_num(res["health"]), fmt_num(res["attack"]), fmt_num(res["rating"]), "待插值补齐")
            else:
                log_msg = f"[{idx}/{len(bot_list)}] ⏩ [抓不到跳过] {bot_name:<20} (将在最后插值编入)"
                row_data = (bot_name, "-", "-", "-", "-", "⏩ 跳过 (待插值)")

            self.root.after(0, lambda msg=log_msg, row=row_data, i=idx: self._on_step_progress(msg, row, i))

        # 3. 插值补齐
        self.root.after(0, lambda: self._log("\n[*] 正在执行插值补齐，确保所有角色均生成 6/60 完整数据..."))

        if exact_660_list:
            avg_hp = round(sum(v["health"] for v in exact_660_list) / len(exact_660_list))
            avg_atk = round(sum(v["attack"] for v in exact_660_list) / len(exact_660_list))
            avg_rat = round(sum(v["rating"] for v in exact_660_list if v["rating"]) / len([v for v in exact_660_list if v["rating"]]))
        else:
            avg_hp, avg_atk, avg_rat = 34500, 2600, 10000

        final_batch = {}
        for bot_name in bot_list:
            if bot_name not in raw_results:
                continue
            wiki_page = bot_name.strip().replace(" ", "_")
            item = raw_results.get(bot_name)

            if item and item["rank_level"] == "6/60":
                final_batch[bot_name] = {
                    "name": bot_name,
                    "wiki_page": wiki_page,
                    "rank_level": "6/60",
                    "match_type": item["match_type"],
                    "health": item["health"],
                    "attack": item["attack"],
                    "rating": item["rating"],
                    "health_str": fmt_num(item["health"]),
                    "attack_str": fmt_num(item["attack"]),
                    "rating_str": fmt_num(item["rating"]),
                }
            elif item and item["rank_level"] == "5/50":
                hp_660 = round(item["health"] * GROWTH_HP_5TO6)
                atk_660 = round(item["attack"] * GROWTH_ATK_5TO6)
                rat_660 = round(item["rating"] * GROWTH_RATING_5TO6) if item["rating"] else avg_rat
                final_batch[bot_name] = {
                    "name": bot_name,
                    "wiki_page": wiki_page,
                    "rank_level": "6/60",
                    "match_type": "interpolated (from 5/50)",
                    "base_5_50": {"health": item["health"], "attack": item["attack"], "rating": item["rating"]},
                    "health": hp_660,
                    "attack": atk_660,
                    "rating": rat_660,
                    "health_str": fmt_num(hp_660),
                    "attack_str": fmt_num(atk_660),
                    "rating_str": fmt_num(rat_660),
                }
                log_s = f"  [+] 为 {bot_name:<20} 插值补齐 6/60 (基于5/50): HP {fmt_num(hp_660)}, ATK {fmt_num(atk_660)}, Rating {fmt_num(rat_660)}"
                row_s = (bot_name, "6/60", fmt_num(hp_660), fmt_num(atk_660), fmt_num(rat_660), "✔ 插值补齐 (基准5/50)")
                self.root.after(0, lambda s=log_s, r=row_s: self._update_tree_row(s, r))
            else:
                final_batch[bot_name] = {
                    "name": bot_name,
                    "wiki_page": wiki_page,
                    "rank_level": "6/60",
                    "match_type": "interpolated (estimated benchmark)",
                    "health": avg_hp,
                    "attack": avg_atk,
                    "rating": avg_rat,
                    "health_str": fmt_num(avg_hp),
                    "attack_str": fmt_num(avg_atk),
                    "rating_str": fmt_num(avg_rat),
                }
                log_s = f"  [+] 为 {bot_name:<20} 插值编入 6/60 (基准估算): HP {fmt_num(avg_hp)}, ATK {fmt_num(avg_atk)}, Rating {fmt_num(avg_rat)}"
                row_s = (bot_name, "6/60", fmt_num(avg_hp), fmt_num(avg_atk), fmt_num(avg_rat), "✔ 插值编入 (估算)")
                self.root.after(0, lambda s=log_s, r=row_s: self._update_tree_row(s, r))

        # 4. 增量合并写入磁盘
        existing_data.update(final_batch)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(existing_data, ensure_ascii=False, indent=2), encoding="utf-8")

        self.root.after(0, lambda: self._on_finish(len(final_batch), len(existing_data), out_path))

    def _on_step_progress(self, msg, row, cur_idx):
        self._log(msg)
        self.tree.insert("", tk.END, iid=row[0], values=row)
        self.prog_bar["value"] = cur_idx

    def _update_tree_row(self, log_msg, row):
        self._log(log_msg)
        bot_name = row[0]
        if self.tree.exists(bot_name):
            self.tree.item(bot_name, values=row)
        else:
            self.tree.insert("", tk.END, iid=bot_name, values=row)

    def _on_finish(self, batch_count, total_count, out_path):
        self.is_running = False
        self.btn_run.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.txt_input.config(state=tk.NORMAL)

        self._log("\n======================================================================")
        self._log(f" ✅ 本次任务完成！已处理: {batch_count} 个角色，JSON 累计保存: {total_count} 个角色")
        self._log(f" 💾 文件路径: {out_path.resolve()}")
        self._log("======================================================================\n")

        self.lbl_status.config(text=f"完成！JSON 累计: {total_count} 个角色")
        messagebox.showinfo("完成", f"抓取与插值全量完成！\n本次写入: {batch_count} 个角色\nJSON 当前总计: {total_count} 个角色\n\n已成功增量保存至:\n{out_path.name}")

def main():
    root = tk.Tk()
    app = ScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
