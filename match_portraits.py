# -*- coding: utf-8 -*-
"""
Transformers: Forged to Fight - 角色头像映射核对工具 (Portrait Selector & Review Tool)
- 支持下拉列表快捷选择 158 个现有 Portrait 资源
- 支持每个角色独立的【自定义输入框】，可直接粘贴/手动输入自定义贴图名或路径
- 下拉框与自定义输入框双向联动，实时展示预览缩略图
- 点击【保存修正清单 (Save Mapping)】一键导出为 Server/bot_portrait_mapping.json
"""

import os
import sys
import json
import http.server
import socketserver
import webbrowser
import urllib.parse

# 强制 UTF-8 环境
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if os.path.join(ROOT_DIR, 'Server') not in sys.path:
    sys.path.insert(0, os.path.join(ROOT_DIR, 'Server'))

try:
    import gamedata
except Exception as e:
    print(f"[Warning] Failed to import gamedata directly: {e}")

PORTRAITS_DIR = os.path.join(ROOT_DIR, "extracted_apk", "assets", "assetpack", "portraits_odr", "portraits")
OUT_JSON_PATH = os.path.join(ROOT_DIR, "Server", "bot_portrait_mapping.json")

# 读取中文名称对照
ZH_NAMES_FILE = os.path.join(ROOT_DIR, "Server", "bot_names_zh.json")
zh_names = {}
if os.path.exists(ZH_NAMES_FILE):
    try:
        with open(ZH_NAMES_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            zh_names = json.load(f)
    except Exception as e:
        print(f"Failed to load bot_names_zh.json: {e}")

def get_all_portraits():
    """获取所有可用的 Portrait 贴图文件"""
    if not os.path.exists(PORTRAITS_DIR):
        return []
    files = sorted(os.listdir(PORTRAITS_DIR))
    portraits = []
    for f in files:
        if f.startswith("portrait_") and (f.endswith("_small.jpg") or f.endswith("_small.png")):
            base = f[len("portrait_"):-len("_small.jpg")] if f.endswith(".jpg") else f[len("portrait_"):-len("_small.png")]
            portraits.append({
                "filename": f,
                "base": base,
                "ext": "jpg" if f.endswith(".jpg") else "png"
            })
    return portraits

def get_all_characters():
    """获取所有游戏角色列表"""
    characters = []
    roster = getattr(gamedata, "ROSTER", {})
    art_base_fn = getattr(gamedata, "art_base", lambda x: x)
    
    for bid, info in roster.items():
        faction, klass, star = info if len(info) >= 3 else ("autobot", "braw", 5)
        current_base = art_base_fn(bid)
        name_zh = zh_names.get(bid, "")
        name_en = getattr(gamedata, "display_name", lambda b, lang="en": b)(bid, lang="en")
        characters.append({
            "bid": bid,
            "name_zh": name_zh,
            "name_en": name_en,
            "faction": faction,
            "class": klass,
            "star": star,
            "current_base": current_base
        })
    return characters

# 预计算初始数据
AVAILABLE_PORTRAITS = get_all_portraits()
PORTRAIT_BASES = [p["base"] for p in AVAILABLE_PORTRAITS]
ALL_CHARACTERS = get_all_characters()

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>角色头像映射核对工具 (TFTF Portrait Selector)</title>
<style>
  :root {
    --bg-main: #14171c;
    --bg-card: #1f242d;
    --bg-card-alt: #272e3a;
    --text-primary: #e6edf3;
    --text-secondary: #8b949e;
    --accent-blue: #388bfd;
    --accent-green: #2ea043;
    --accent-orange: #d29922;
    --accent-red: #f85149;
    --border-color: #30363d;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: var(--bg-main);
    color: var(--text-primary);
    padding: 20px;
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 20px;
    position: sticky;
    top: 0;
    background: var(--bg-main);
    z-index: 100;
  }
  .title-group h1 { font-size: 22px; font-weight: 700; color: #fff; }
  .title-group p { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
  .actions { display: flex; gap: 12px; align-items: center; }
  .search-input {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    color: #fff;
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 14px;
    width: 260px;
  }
  .btn {
    padding: 8px 18px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
  }
  .btn-primary { background: var(--accent-green); color: #fff; }
  .btn-primary:hover { background: #3fb950; }
  .btn-secondary { background: var(--accent-blue); color: #fff; }
  .btn-secondary:hover { background: #58a6ff; }
  
  .stats-bar {
    display: flex;
    gap: 20px;
    background: var(--bg-card);
    padding: 12px 18px;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    margin-bottom: 20px;
    font-size: 14px;
  }
  .stat-item span { font-weight: 700; color: var(--accent-blue); }

  .character-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(480px, 1fr));
    gap: 16px;
  }
  .card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 14px 16px;
    display: flex;
    align-items: center;
    gap: 16px;
    transition: border-color 0.2s, background 0.2s;
  }
  .card:hover { border-color: var(--accent-blue); }
  .card.unmatched { border-color: var(--accent-orange); background: #262117; }
  
  .avatar-wrap {
    width: 80px;
    height: 80px;
    border-radius: 8px;
    overflow: hidden;
    background: #0d1117;
    border: 2px solid var(--border-color);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .avatar-wrap img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  .avatar-wrap .no-img {
    font-size: 11px;
    color: var(--accent-red);
    text-align: center;
  }
  
  .card-info { flex: 1; min-width: 0; }
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 4px;
  }
  .bot-name {
    font-size: 15px;
    font-weight: 700;
    color: #fff;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .bot-zh { color: var(--accent-orange); font-size: 13px; margin-left: 6px; }
  .bot-id {
    font-size: 12px;
    color: var(--text-secondary);
    font-family: monospace;
    margin-bottom: 8px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .control-row {
    display: flex;
    gap: 8px;
    align-items: center;
    margin-bottom: 6px;
  }
  .control-row:last-child { margin-bottom: 0; }
  .control-label {
    font-size: 11px;
    color: var(--text-secondary);
    width: 44px;
    flex-shrink: 0;
  }
  .portrait-select, .custom-input {
    flex: 1;
    background: var(--bg-main);
    border: 1px solid var(--border-color);
    color: #fff;
    padding: 5px 8px;
    border-radius: 5px;
    font-size: 12px;
    font-family: monospace;
    outline: none;
  }
  .portrait-select { cursor: pointer; }
  .portrait-select:focus, .custom-input:focus { border-color: var(--accent-blue); }
  .custom-input { color: #58a6ff; }
  .custom-input::placeholder { color: #484f58; font-family: sans-serif; font-size: 11px; }

  .status-tag {
    font-size: 11px;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 600;
  }
  .tag-autobot { background: rgba(56, 139, 253, 0.2); color: #58a6ff; }
  .tag-decepticon { background: rgba(163, 113, 247, 0.2); color: #bc8cff; }

  #toast {
    position: fixed;
    bottom: 30px;
    right: 30px;
    background: var(--accent-green);
    color: #fff;
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: 600;
    box-shadow: 0 4px 16px rgba(0,0,0,0.5);
    opacity: 0;
    transform: translateY(20px);
    transition: all 0.3s;
    pointer-events: none;
    z-index: 1000;
  }
  #toast.show { opacity: 1; transform: translateY(0); }
</style>
</head>
<body>

<header>
  <div class="title-group">
    <h1>角色头像映射核对工具 (Portrait Mapping Tool)</h1>
    <p>可从下拉列表中选取，也可在自定义输入框中直接填写/粘贴任意贴图文件名或路径。</p>
  </div>
  <div class="actions">
    <input type="text" id="searchInput" class="search-input" placeholder="🔍 搜索角色名称 / ID / 拼音..." oninput="filterCards()">
    <button class="btn btn-secondary" onclick="autoSuggest()">⚡ 智能自动匹配</button>
    <button class="btn btn-primary" onclick="saveMapping()">💾 保存修正清单</button>
  </div>
</header>

<div class="stats-bar">
  <div class="stat-item">总角色数: <span id="totalCount">0</span></div>
  <div class="stat-item">已指定贴图: <span id="matchedCount">0</span></div>
  <div class="stat-item">未指定 / 缺失: <span id="unmatchedCount" style="color:var(--accent-orange)">0</span></div>
  <div class="stat-item">贴图资源库总量: <span id="portraitPoolCount">0</span> 份</div>
</div>

<div class="character-grid" id="charGrid"></div>

<div id="toast">✅ 修正清单已保存至 Server/bot_portrait_mapping.json</div>

<script>
let characters = [];
let availablePortraits = [];

async function loadData() {
  const resp = await fetch('/api/data');
  const data = await resp.json();
  characters = data.characters;
  availablePortraits = data.portraits;
  render();
}

function render() {
  const grid = document.getElementById('charGrid');
  grid.innerHTML = '';
  
  let specified = 0;
  const portraitSet = new Set(availablePortraits.map(p => p.base));
  
  document.getElementById('totalCount').innerText = characters.length;
  document.getElementById('portraitPoolCount').innerText = availablePortraits.length;

  characters.forEach((char, idx) => {
    const hasVal = Boolean(char.current_base && char.current_base.trim());
    if (hasVal) specified++;

    const card = document.createElement('div');
    card.className = `card ${hasVal ? '' : 'unmatched'}`;
    card.id = `card-${char.bid}`;
    card.dataset.name = `${char.bid} ${char.name_zh} ${char.name_en}`.toLowerCase();

    // 贴图 URL
    const imgUrl = hasVal ? `/portrait/${encodeURIComponent(char.current_base)}` : '';

    let optionsHtml = `<option value="">-- 从已有库选择 --</option>`;
    availablePortraits.forEach(p => {
      const selected = (p.base === char.current_base) ? 'selected' : '';
      optionsHtml += `<option value="${p.base}" ${selected}>${p.filename} (${p.base})</option>`;
    });

    card.innerHTML = `
      <div class="avatar-wrap" id="img-wrap-${char.bid}">
        ${hasVal ? `<img src="${imgUrl}" id="img-${char.bid}" alt="portrait" onerror="handleImgError('${char.bid}')">` : `<div class="no-img" id="img-${char.bid}">无图片</div>`}
      </div>
      <div class="card-info">
        <div class="card-header">
          <div class="bot-name">
            ${char.name_en}
            ${char.name_zh ? `<span class="bot-zh">${char.name_zh}</span>` : ''}
          </div>
          <span class="status-tag tag-${char.faction}">${char.faction.toUpperCase()}</span>
        </div>
        <div class="bot-id">ID: ${char.bid}</div>
        
        <div class="control-row">
          <span class="control-label">下拉选:</span>
          <select class="portrait-select" id="select-${char.bid}" onchange="onSelectChange('${char.bid}', this.value)">
            ${optionsHtml}
          </select>
        </div>
        
        <div class="control-row">
          <span class="control-label">自定义:</span>
          <input type="text" class="custom-input" id="input-${char.bid}" value="${char.current_base || ''}" placeholder="手动输入贴图前缀/路径..." oninput="onInputChange('${char.bid}', this.value)">
        </div>
      </div>
    `;
    grid.appendChild(card);
  });

  document.getElementById('matchedCount').innerText = specified;
  document.getElementById('unmatchedCount').innerText = characters.length - specified;
}

function handleImgError(bid) {
  const wrap = document.getElementById(`img-wrap-${bid}`);
  wrap.innerHTML = `<div class="no-img">暂无贴图</div>`;
}

function updateCardPreview(bid, val) {
  const wrap = document.getElementById(`img-wrap-${bid}`);
  const card = document.getElementById(`card-${bid}`);

  if (val && val.trim()) {
    wrap.innerHTML = `<img src="/portrait/${encodeURIComponent(val.trim())}?t=${Date.now()}" id="img-${bid}" alt="portrait" onerror="handleImgError('${bid}')">`;
    card.classList.remove('unmatched');
  } else {
    wrap.innerHTML = `<div class="no-img">无图片</div>`;
    card.classList.add('unmatched');
  }
  updateStats();
}

function onSelectChange(bid, newBase) {
  const char = characters.find(c => c.bid === bid);
  if (!char) return;
  char.current_base = newBase;

  const input = document.getElementById(`input-${bid}`);
  if (input) input.value = newBase;

  updateCardPreview(bid, newBase);
}

function onInputChange(bid, customVal) {
  const char = characters.find(c => c.bid === bid);
  if (!char) return;
  char.current_base = customVal.trim();

  // 如果输入的内容正好匹配下拉列表中的某项，同步下拉选中状态
  const select = document.getElementById(`select-${bid}`);
  if (select) {
    select.value = char.current_base;
  }

  updateCardPreview(bid, char.current_base);
}

function updateStats() {
  let specified = 0;
  characters.forEach(c => {
    if (c.current_base && c.current_base.trim()) specified++;
  });
  document.getElementById('matchedCount').innerText = specified;
  document.getElementById('unmatchedCount').innerText = characters.length - specified;
}

function filterCards() {
  const query = document.getElementById('searchInput').value.trim().toLowerCase();
  characters.forEach(c => {
    const card = document.getElementById(`card-${c.bid}`);
    if (!card) return;
    if (!query || card.dataset.name.includes(query)) {
      card.style.display = 'flex';
    } else {
      card.style.display = 'none';
    }
  });
}

function autoSuggest() {
  const portraitBases = availablePortraits.map(p => p.base);
  characters.forEach(c => {
    if (!c.current_base || !c.current_base.trim()) {
      const parts = c.bid.split('_');
      const prefix = parts[0];
      const match = portraitBases.find(b => b.startsWith(prefix) || b.includes(prefix));
      if (match) {
        c.current_base = match;
        const sel = document.getElementById(`select-${c.bid}`);
        if (sel) sel.value = match;
        const input = document.getElementById(`input-${c.bid}`);
        if (input) input.value = match;
        updateCardPreview(c.bid, match);
      }
    }
  });
  updateStats();
  showToast('⚡ 自动模糊匹配完成，请复核变更！');
}

async function saveMapping() {
  const mapping = {};
  characters.forEach(c => {
    if (c.current_base && c.current_base.trim()) {
      mapping[c.bid] = c.current_base.trim();
    }
  });
  
  const resp = await fetch('/api/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(mapping, null, 2)
  });
  const res = await resp.json();
  if (res.ok) {
    showToast('💾 映射表已成功保存至 Server/bot_portrait_mapping.json !');
  } else {
    alert('保存失败: ' + res.error);
  }
}

function showToast(msg) {
  const toast = document.getElementById('toast');
  toast.innerText = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3500);
}

loadData();
</script>
</body>
</html>
"""

def find_portrait_file_on_disk(base_or_path):
    """灵活匹配各种贴图文件名/路径"""
    name = base_or_path.strip().replace('\\', '/')
    
    # 1. 尝试标准 portrait_<base>_small.jpg / .png
    for ext in ['.jpg', '.png']:
        cand = os.path.join(PORTRAITS_DIR, f"portrait_{name}_small{ext}")
        if os.path.exists(cand):
            return cand
            
    # 2. 尝试 portrait_<base>_large.png / .jpg
    for ext in ['.png', '.jpg']:
        cand = os.path.join(PORTRAITS_DIR, f"portrait_{name}_large{ext}")
        if os.path.exists(cand):
            return cand

    # 3. 尝试直接作为 portraits_odr 下的文件名
    cand = os.path.join(PORTRAITS_DIR, name)
    if os.path.exists(cand) and os.path.isfile(cand):
        return cand

    # 4. 尝试 assetpack 下的文件
    assetpack_dir = os.path.join(ROOT_DIR, "extracted_apk", "assets", "assetpack")
    cand = os.path.join(assetpack_dir, name)
    if os.path.exists(cand) and os.path.isfile(cand):
        return cand

    # 5. 尝试 assets 下的文件
    assets_dir = os.path.join(ROOT_DIR, "extracted_apk", "assets")
    cand = os.path.join(assets_dir, name)
    if os.path.exists(cand) and os.path.isfile(cand):
        return cand

    return None

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # 静默控制台请求日志

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        if path == '/' or path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
            return

        if path == '/api/data':
            saved_map = {}
            if os.path.exists(OUT_JSON_PATH):
                try:
                    with open(OUT_JSON_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                        saved_map = json.load(f)
                except:
                    pass

            chars = [dict(c) for c in ALL_CHARACTERS]
            for c in chars:
                if c["bid"] in saved_map:
                    c["current_base"] = saved_map[c["bid"]]

            payload = {
                "characters": chars,
                "portraits": AVAILABLE_PORTRAITS
            }
            body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path.startswith('/portrait/'):
            raw = path[len('/portrait/'):]
            base_or_path = urllib.parse.unquote(raw)
            target_file = find_portrait_file_on_disk(base_or_path)
            
            if target_file and os.path.exists(target_file):
                self.send_response(200)
                content_type = 'image/png' if target_file.endswith('.png') else 'image/jpeg'
                self.send_header('Content-Type', content_type)
                with open(target_file, 'rb') as fp:
                    data = fp.read()
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            else:
                self.send_response(404)
                self.end_headers()
                return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/save':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            try:
                mapping = json.loads(body)
                with open(OUT_JSON_PATH, 'w', encoding='utf-8') as f:
                    json.dump(mapping, f, ensure_ascii=False, indent=2)
                print(f"\n[Success] Updated portrait mapping saved to: {OUT_JSON_PATH} ({len(mapping)} bots)")
                resp = json.dumps({"ok": True, "count": len(mapping)}).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                resp = json.dumps({"ok": False, "error": str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(resp)
            return

def start_tk():
    """Tkinter 桌面原生窗口模式（支持自由键入）"""
    import tkinter as tk
    from tkinter import ttk, messagebox

    root = tk.Tk()
    root.title("TFTF 角色头像映射核对工具 (Tkinter)")
    root.geometry("950x700")

    saved_map = {}
    if os.path.exists(OUT_JSON_PATH):
        try:
            with open(OUT_JSON_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                saved_map = json.load(f)
        except:
            pass

    chars = [dict(c) for c in ALL_CHARACTERS]
    combos = {}

    top_frame = ttk.Frame(root, padding=10)
    top_frame.pack(fill=tk.X)
    
    ttk.Label(top_frame, text="角色头像映射核对清单 (可下拉选择或直接键入自定义路径)", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT)
    
    def save_tk():
        mapping = {}
        for c in chars:
            val = combos[c["bid"]].get().strip()
            if val:
                mapping[c["bid"]] = val
        try:
            with open(OUT_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", f"修正清单已保存至:\n{OUT_JSON_PATH}\n(共 {len(mapping)} 个角色)")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")

    ttk.Button(top_frame, text="💾 保存修正清单", command=save_tk).pack(side=tk.RIGHT)

    container = ttk.Frame(root)
    container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scroll_frame = ttk.Frame(canvas)

    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # 表头
    header_frame = ttk.Frame(scroll_frame, padding=5)
    header_frame.pack(fill=tk.X)
    ttk.Label(header_frame, text="角色全名 (bid)", width=32, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
    ttk.Label(header_frame, text="中文名 / 英文名", width=25, font=("Segoe UI", 9, "bold")).grid(row=0, column=1, sticky="w")
    ttk.Label(header_frame, text="Portrait 贴图名称 (可直接键入)", width=35, font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w")

    portrait_options = [""] + PORTRAIT_BASES

    for idx, char in enumerate(chars):
        row_frame = ttk.Frame(scroll_frame, padding=4)
        row_frame.pack(fill=tk.X, pady=2)
        
        bid = char["bid"]
        zh = char["name_zh"] or char["name_en"]
        curr = saved_map.get(bid, char["current_base"])

        ttk.Label(row_frame, text=bid, width=32, font=("Consolas", 9)).grid(row=0, column=0, sticky="w")
        ttk.Label(row_frame, text=f"{zh} ({char['faction'][:3].upper()})", width=25).grid(row=0, column=1, sticky="w")
        
        cb = ttk.Combobox(row_frame, values=portrait_options, width=32, state="normal")
        cb.set(curr if curr else "")
        cb.grid(row=0, column=2, sticky="w")
        combos[bid] = cb

    root.mainloop()

def start_server():
    port = 8899
    while port < 8999:
        try:
            httpd = socketserver.TCPServer(('127.0.0.1', port), RequestHandler)
            break
        except OSError:
            port += 1

    url = f"http://127.0.0.1:{port}"
    print("=" * 70)
    print("  🚀 TFTF 角色头像可视化映射与核对工具已更新！")
    print(f"  🌐 访问地址: {url}")
    print("  👉 每个角色现已增加【自定义输入框】，可直接粘贴或输入任意贴图路径！")
    print("  👉 核对完成后，点击右上角【💾 保存修正清单】即可写入配置。")
    print("  🛑 按 Ctrl+C 可停止工具服务器。")
    print("=" * 70)

    webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n工具已关闭。")
        httpd.server_close()

if __name__ == '__main__':
    if "--tk" in sys.argv:
        start_tk()
    else:
        start_server()
