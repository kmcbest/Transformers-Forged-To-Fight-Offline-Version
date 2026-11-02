import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import json
from pathlib import Path

# Read tools/basic_abilities.json
json_path = Path("tools/basic_abilities.json")
with open(json_path, "r", encoding="utf-8") as f:
    catalog_data = json.load(f)

json_str = json.dumps(catalog_data, ensure_ascii=False)

html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TFTF 基础能力（Basic Abilities）总览与修订工作台</title>
    <style>
        @font-face {
            font-family: 'Tecnica';
            src: url('Tecnica_Bold_116.ttf') format('truetype');
        }

        :root {
            --bg-main: #0B0E14;
            --bg-card: #151A23;
            --bg-card-hover: #1E2532;
            --bg-darker: #080A0F;
            --border-color: #262F40;
            --border-hover: #3B82F6;
            --text-main: #F1F5F9;
            --text-muted: #94A3B8;
            --text-sub: #64748B;
            --primary: #3B82F6;
            --primary-glow: rgba(59, 130, 246, 0.25);
            --success: #10B981;
            --warning: #F59E0B;
            --danger: #EF4444;
            --purple: #8B5CF6;
            --cyan: #06B6D4;
            --tact-color: #0543EF;
            --braw-color: #7D34BC;
            --warr-color: #E9312D;
            --scou-color: #1D9F06;
            --tech-color: #09BCDD;
            --demo-color: #F5BD0D;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-main);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans SC", sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* Top Header */
        header {
            background: linear-gradient(180deg, #121824 0%, #0D121B 100%);
            border-bottom: 1px solid var(--border-color);
            padding: 16px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }

        .header-title {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .logo-badge {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #2563EB, #7C3AED);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Tecnica', sans-serif;
            font-size: 24px;
            color: #fff;
            box-shadow: 0 0 15px var(--primary-glow);
        }

        .title-text h1 {
            font-size: 20px;
            font-weight: 700;
            color: #FFF;
            letter-spacing: 0.5px;
        }

        .title-text p {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 2px;
        }

        .header-actions {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        button {
            cursor: pointer;
            border: none;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            padding: 8px 14px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s ease;
        }

        .btn-primary {
            background: #2563EB;
            color: #FFF;
        }
        .btn-primary:hover {
            background: #1D4ED8;
            box-shadow: 0 0 12px rgba(37, 99, 235, 0.4);
        }

        .btn-success {
            background: #059669;
            color: #FFF;
        }
        .btn-success:hover {
            background: #047857;
            box-shadow: 0 0 12px rgba(5, 150, 105, 0.4);
        }

        .btn-secondary {
            background: #1E2532;
            color: var(--text-main);
            border: 1px solid var(--border-color);
        }
        .btn-secondary:hover {
            background: #2B3445;
            border-color: #475569;
        }

        .btn-danger {
            background: #DC2626;
            color: #FFF;
        }
        .btn-danger:hover {
            background: #B91C1C;
        }

        /* Stats bar */
        .stats-bar {
            background: var(--bg-card);
            border-bottom: 1px solid var(--border-color);
            padding: 12px 32px;
            display: flex;
            gap: 32px;
            font-size: 13px;
            align-items: center;
        }

        .stat-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .stat-val {
            font-size: 16px;
            font-weight: 700;
            color: #38BDF8;
        }

        /* Main Container */
        .container {
            padding: 24px 32px;
            max-width: 1600px;
            margin: 0 auto;
            width: 100%;
            flex: 1;
        }

        /* Controls: Search, Categories, Views */
        .controls-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }

        .search-box {
            position: relative;
            flex: 1;
            min-width: 320px;
            max-width: 480px;
        }

        .search-box input {
            width: 100%;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 10px 14px 10px 38px;
            color: var(--text-main);
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }

        .search-box input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 10px var(--primary-glow);
        }

        .search-icon {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-sub);
            font-size: 15px;
        }

        .view-switch {
            display: flex;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            overflow: hidden;
        }

        .view-btn {
            background: transparent;
            color: var(--text-muted);
            border: none;
            padding: 8px 14px;
            font-size: 13px;
            border-radius: 0;
        }

        .view-btn.active {
            background: #2563EB;
            color: #FFF;
        }

        /* Category pills */
        .category-filters {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }

        .cat-pill {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s;
        }

        .cat-pill:hover {
            border-color: var(--text-muted);
            color: var(--text-main);
        }

        .cat-pill.active {
            background: var(--primary);
            border-color: var(--primary);
            color: #FFF;
            box-shadow: 0 0 10px var(--primary-glow);
        }

        /* Table View */
        .table-wrap {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            overflow-x: auto;
            box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 13px;
        }

        th {
            background: #111620;
            color: var(--text-muted);
            padding: 14px 16px;
            font-weight: 600;
            border-bottom: 1px solid var(--border-color);
            white-space: nowrap;
        }

        td {
            padding: 12px 16px;
            border-bottom: 1px solid #1C2331;
            vertical-align: middle;
        }

        tr:hover td {
            background: var(--bg-card-hover);
        }

        .pua-glyph {
            font-family: 'Tecnica', -apple-system, sans-serif;
            font-size: 26px;
            color: #38BDF8;
            display: inline-block;
            vertical-align: middle;
            min-width: 32px;
            text-align: center;
        }

        .pua-hex-badge {
            display: inline-block;
            background: #0D121B;
            border: 1px solid #262F40;
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 11px;
            font-family: monospace;
            color: #94A3B8;
            margin-left: 6px;
        }

        .name-cell {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .name-zh {
            font-weight: 700;
            color: #F8FAFC;
            font-size: 14px;
        }

        .name-en {
            font-size: 11px;
            color: var(--text-sub);
        }

        .cat-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            background: #1E293B;
            color: #94A3B8;
            border: 1px solid #334155;
        }

        .cat-持续伤害 { background: rgba(239, 68, 68, 0.15); color: #FCA5A5; border-color: rgba(239, 68, 68, 0.4); }
        .cat-防御削弱 { background: rgba(245, 158, 11, 0.15); color: #FCD34D; border-color: rgba(245, 158, 11, 0.4); }
        .cat-属性增益 { background: rgba(16, 185, 129, 0.15); color: #6EE7B7; border-color: rgba(16, 185, 129, 0.4); }
        .cat-行动控制 { background: rgba(139, 92, 246, 0.15); color: #C4B5FD; border-color: rgba(139, 92, 246, 0.4); }
        .cat-能量控制 { background: rgba(6, 182, 212, 0.15); color: #67E8F9; border-color: rgba(6, 182, 212, 0.4); }
        .cat-机动防御 { background: rgba(59, 130, 246, 0.15); color: #93C5FD; border-color: rgba(59, 130, 246, 0.4); }
        .cat-生存防御 { background: rgba(14, 165, 233, 0.15); color: #7DD3FC; border-color: rgba(14, 165, 233, 0.4); }
        .cat-机制克制 { background: rgba(236, 72, 153, 0.15); color: #F472B6; border-color: rgba(236, 72, 153, 0.4); }

        .desc-text {
            color: #E2E8F0;
            line-height: 1.5;
            max-width: 480px;
        }

        .bot-count-btn {
            background: #111827;
            border: 1px solid #374151;
            color: #9CA3AF;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            cursor: pointer;
            transition: all 0.15s;
            white-space: nowrap;
        }

        .bot-count-btn:hover {
            border-color: #60A5FA;
            color: #60A5FA;
            background: rgba(37, 99, 235, 0.15);
        }

        /* Card View */
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
            gap: 16px;
        }

        .ability-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            transition: transform 0.2s, border-color 0.2s;
            position: relative;
        }

        .ability-card:hover {
            border-color: var(--primary);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.4);
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .card-icon-box {
            width: 48px;
            height: 48px;
            background: #0E131E;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Tecnica', sans-serif;
            font-size: 30px;
            color: #38BDF8;
        }

        .card-title-group {
            flex: 1;
        }

        .card-title-group h3 {
            font-size: 16px;
            font-weight: 700;
            color: #FFF;
        }

        .card-title-group .sub {
            font-size: 11px;
            color: var(--text-sub);
        }

        .card-body {
            font-size: 13px;
            color: #E2E8F0;
            line-height: 1.5;
            background: #0F141E;
            padding: 10px 12px;
            border-radius: 6px;
            border: 1px solid #1C2331;
            flex: 1;
        }

        .card-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 4px;
            font-size: 12px;
        }

        /* Modal Styles */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.75);
            backdrop-filter: blur(4px);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            padding: 20px;
        }

        .modal-overlay.active {
            display: flex;
        }

        .modal-box {
            background: #131822;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            width: 100%;
            max-width: 640px;
            max-height: 90vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 10px 30px rgba(0,0,0,0.8);
            animation: modalIn 0.2s ease-out;
        }

        @keyframes modalIn {
            from { opacity: 0; transform: scale(0.95); }
            to { opacity: 1; transform: scale(1); }
        }

        .modal-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-header h2 {
            font-size: 17px;
            font-weight: 700;
            color: #FFF;
        }

        .close-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 20px;
            cursor: pointer;
            padding: 4px;
        }

        .close-btn:hover {
            color: #FFF;
        }

        .modal-body {
            padding: 20px;
            overflow-y: auto;
            flex: 1;
        }

        .form-group {
            margin-bottom: 16px;
        }

        .form-group label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 6px;
        }

        .form-control {
            width: 100%;
            background: #0B0E14;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 8px 12px;
            color: var(--text-main);
            font-size: 13px;
            outline: none;
            transition: border-color 0.2s;
        }

        .form-control:focus {
            border-color: var(--primary);
        }

        textarea.form-control {
            resize: vertical;
            min-height: 80px;
            line-height: 1.5;
        }

        .icon-selector-grid {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 8px;
        }

        .icon-pill-btn {
            background: #0B0E14;
            border: 1px solid var(--border-color);
            color: #E2E8F0;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .icon-pill-btn:hover {
            border-color: var(--primary);
            background: #1E2532;
        }

        .modal-footer {
            padding: 14px 20px;
            border-top: 1px solid var(--border-color);
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            background: #0E121B;
            border-radius: 0 0 12px 12px;
        }

        /* Bot association selector inside modal */
        .bot-search-bar {
            margin-bottom: 12px;
        }

        .bot-pills-container {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            max-height: 360px;
            overflow-y: auto;
            padding: 4px;
        }

        .bot-check-label {
            background: #0B0E14;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.15s;
        }

        .bot-check-label:hover {
            border-color: #475569;
        }

        .bot-check-label.selected {
            background: rgba(37, 99, 235, 0.2);
            border-color: #3B82F6;
            color: #60A5FA;
        }

        /* Toast */
        .toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #1E293B;
            color: #FFF;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.6);
            border-left: 4px solid var(--primary);
            font-size: 13px;
            z-index: 2000;
            display: none;
            animation: fadeIn 0.2s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Hidden file input */
        #import-file-input {
            display: none;
        }
    </style>
</head>
<body>

    <!-- Header -->
    <header>
        <div class="header-title">
            <div class="logo-badge">⚡</div>
            <div class="title-text">
                <h1>TFTF 基础能力（Basic Abilities）总览与修订工作台</h1>
                <p>公用描述与状态机制字典库 · 严禁写死数值与特定触发条件 · 纯净规范化</p>
            </div>
        </div>
        <div class="header-actions">
            <input type="file" id="import-file-input" accept=".json">
            <button class="btn-secondary" onclick="document.getElementById('import-file-input').click()">
                📥 导入 JSON
            </button>
            <button class="btn-primary" onclick="exportJSON()">
                📤 导出 JSON
            </button>
            <button class="btn-secondary" onclick="copyFullJSON()">
                📋 复制 JSON
            </button>
            <button class="btn-success" onclick="openAddModal()">
                ➕ 新增能力
            </button>
            <button class="btn-secondary" onclick="resetToDefault()">
                🔄 恢复默认
            </button>
        </div>
    </header>

    <!-- Stats Bar -->
    <div class="stats-bar">
        <div class="stat-item">
            <span>基础能力总数:</span>
            <span class="stat-val" id="stat-total">0</span>
        </div>
        <div class="stat-item">
            <span>覆盖英雄总数:</span>
            <span class="stat-val" id="stat-bots">0</span>
        </div>
        <div class="stat-item">
            <span>能力分类大系:</span>
            <span class="stat-val" id="stat-cats">0</span>
        </div>
        <div class="stat-item" style="margin-left: auto; color: var(--text-muted); font-size: 12px;">
            <span>💡 提示：所有修改均在本地实时自动暂存，点击【导出 JSON】即可保存定稿文件。</span>
        </div>
    </div>

    <!-- Main Container -->
    <div class="container">
        
        <!-- Controls Row -->
        <div class="controls-row">
            <div class="search-box">
                <span class="search-icon">🔍</span>
                <input type="text" id="search-input" placeholder="搜索名称、简短描述、PUA编码、关联英雄..." oninput="handleSearch()">
            </div>
            
            <div class="view-switch">
                <button class="view-btn active" id="view-table-btn" onclick="switchView('table')">📄 表格精修</button>
                <button class="view-btn" id="view-cards-btn" onclick="switchView('cards')">🃏 卡片浏览</button>
            </div>
        </div>

        <!-- Category Filters -->
        <div class="category-filters" id="cat-filters">
            <!-- Dynamically populated -->
        </div>

        <!-- Table View Container -->
        <div class="table-wrap" id="table-container">
            <table>
                <thead>
                    <tr>
                        <th style="width: 80px;">图标</th>
                        <th style="width: 160px;">能力名称</th>
                        <th style="width: 120px;">分类</th>
                        <th>简短公用描述（原版风格，无数值与触发）</th>
                        <th style="width: 130px; text-align: center;">关联角色</th>
                        <th style="width: 120px; text-align: center;">操作</th>
                    </tr>
                </thead>
                <tbody id="abilities-table-body">
                    <!-- Populated by JS -->
                </tbody>
            </table>
        </div>

        <!-- Cards View Container -->
        <div class="cards-grid" id="cards-container" style="display: none;">
            <!-- Populated by JS -->
        </div>

    </div>

    <!-- Edit/Add Modal -->
    <div class="modal-overlay" id="edit-modal">
        <div class="modal-box">
            <div class="modal-header">
                <h2 id="modal-title">编辑基础能力</h2>
                <button class="close-btn" onclick="closeEditModal()">×</button>
            </div>
            <div class="modal-body">
                <input type="hidden" id="edit-id">
                
                <div style="display: flex; gap: 12px;">
                    <div class="form-group" style="flex: 1;">
                        <label>中文名称 (name_zh)</label>
                        <input type="text" class="form-control" id="edit-name-zh" placeholder="如：流血">
                    </div>
                    <div class="form-group" style="flex: 1;">
                        <label>英文名称 (name_en)</label>
                        <input type="text" class="form-control" id="edit-name-en" placeholder="如：Bleed">
                    </div>
                </div>

                <div style="display: flex; gap: 12px;">
                    <div class="form-group" style="flex: 1;">
                        <label>类别 (category)</label>
                        <select class="form-control" id="edit-category">
                            <option value="持续伤害">持续伤害</option>
                            <option value="防御削弱">防御削弱</option>
                            <option value="属性增益">属性增益</option>
                            <option value="行动控制">行动控制</option>
                            <option value="机动防御">机动防御</option>
                            <option value="能量控制">能量控制</option>
                            <option value="机制克制">机制克制</option>
                            <option value="生存防御">生存防御</option>
                            <option value="生存反制">生存反制</option>
                            <option value="进攻强化">进攻强化</option>
                            <option value="攻击特长">攻击特长</option>
                            <option value="特殊机制">特殊机制</option>
                            <option value="状态减益">状态减益</option>
                            <option value="高风险增益">高风险增益</option>
                        </select>
                    </div>
                    <div class="form-group" style="flex: 1;">
                        <label>PUA 图标编码 (16进制，如 E401)</label>
                        <div style="display: flex; gap: 6px; align-items: center;">
                            <input type="text" class="form-control" id="edit-pua-icon" placeholder="E401" oninput="updateModalIconPreview()">
                            <span class="pua-glyph" id="modal-icon-preview" style="font-size: 28px;"></span>
                        </div>
                    </div>
                </div>

                <div class="form-group">
                    <label>常用图标快速拾取</label>
                    <div class="icon-selector-grid">
                        <span class="icon-pill-btn" onclick="selectQuickIcon('E401')"><span class="pua-glyph" style="font-size: 16px;">\\uE401</span> 流血 (E401)</span>
                        <span class="icon-pill-btn" onclick="selectQuickIcon('E41D')"><span class="pua-glyph" style="font-size: 16px;">\\uE41D</span> 燃烧 (E41D)</span>
                        <span class="icon-pill-btn" onclick="selectQuickIcon('E914')"><span class="pua-glyph" style="font-size: 16px;">\\uE914</span> 震击 (E914)</span>
                        <span class="icon-pill-btn" onclick="selectQuickIcon('E524')"><span class="pua-glyph" style="font-size: 16px;">\\uE524</span> 酸液 (E524)</span>
                        <span class="icon-pill-btn" onclick="selectQuickIcon('E516')"><span class="pua-glyph" style="font-size: 16px;">\\uE516</span> 破甲 (E516)</span>
                        <span class="icon-pill-btn" onclick="selectQuickIcon('E517')"><span class="pua-glyph" style="font-size: 16px;">\\uE517</span> 护甲 (E517)</span>
                        <span class="icon-pill-btn" onclick="selectQuickIcon('E605')"><span class="pua-glyph" style="font-size: 16px;">\\uE605</span> 眩晕 (E605)</span>
                        <span class="icon-pill-btn" onclick="selectQuickIcon('E509')"><span class="pua-glyph" style="font-size: 16px;">\\uE509</span> 规避 (E509)</span>
                        <span class="icon-pill-btn" onclick="selectQuickIcon('E915')"><span class="pua-glyph" style="font-size: 16px;">\\uE915</span> 霸体 (E915)</span>
                        <span class="icon-pill-btn" onclick="selectQuickIcon('E608')"><span class="pua-glyph" style="font-size: 16px;">\\uE608</span> 能量 (E608)</span>
                        <span class="icon-pill-btn" onclick="selectQuickIcon('E607')"><span class="pua-glyph" style="font-size: 16px;">\\uE607</span> 流失 (E607)</span>
                        <span class="icon-pill-btn" onclick="selectQuickIcon('E950')"><span class="pua-glyph" style="font-size: 16px;">\\uE950</span> 驱散 (E950)</span>
                        <span class="icon-pill-btn" onclick="selectQuickIcon('E503')"><span class="pua-glyph" style="font-size: 16px;">\\uE503</span> 修复 (E503)</span>
                        <span class="icon-pill-btn" onclick="selectQuickIcon('E952')"><span class="pua-glyph" style="font-size: 16px;">\\uE952</span> 减速 (E952)</span>
                    </div>
                </div>

                <div class="form-group">
                    <label>中文简短描述（严禁包含百分比、具体数值、持续秒数、特殊触发，只描述公用机制）</label>
                    <textarea class="form-control" id="edit-desc-zh" placeholder="如：流失的能量晶体会持续造成直接伤害。"></textarea>
                </div>

                <div class="form-group">
                    <label>英文简短描述</label>
                    <textarea class="form-control" id="edit-desc-en" placeholder="Bleeding energon causes direct damage over time."></textarea>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-secondary" onclick="closeEditModal()">取消</button>
                <button class="btn-primary" onclick="saveAbilityModal()">保存修改</button>
            </div>
        </div>
    </div>

    <!-- Bot Association Modal -->
    <div class="modal-overlay" id="bots-modal">
        <div class="modal-box" style="max-width: 720px;">
            <div class="modal-header">
                <h2 id="bots-modal-title">关联英雄配置</h2>
                <button class="close-btn" onclick="closeBotsModal()">×</button>
            </div>
            <div class="modal-body">
                <div class="bot-search-bar" style="display: flex; gap: 10px;">
                    <input type="text" class="form-control" id="modal-bot-search" placeholder="在 80 位英雄中搜索并勾选..." oninput="filterModalBots()">
                    <button class="btn-secondary" onclick="toggleSelectAllBots(true)">全选</button>
                    <button class="btn-secondary" onclick="toggleSelectAllBots(false)">清空</button>
                </div>
                <div class="bot-pills-container" id="modal-bot-pills">
                    <!-- Populated dynamically -->
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-secondary" onclick="closeBotsModal()">取消</button>
                <button class="btn-primary" onclick="saveBotsModal()">确定关联</button>
            </div>
        </div>
    </div>

    <!-- Toast -->
    <div class="toast" id="toast"></div>

    <script>
        // Initial Data embedded
        const INITIAL_CATALOG = """ + json_str + """;

        // Working State
        let catalog = null;
        let activeCategory = 'all';
        let searchQuery = '';
        let currentView = 'table';
        let editingAbilityId = null;
        let managingBotsAbilityId = null;
        let tempSelectedBots = new Set();

        // Load data from localStorage or fallback
        function initData() {
            const saved = localStorage.getItem('tftf_basic_abilities_draft');
            if (saved) {
                try {
                    catalog = JSON.parse(saved);
                } catch(e) {
                    console.error('Failed to parse localStorage data:', e);
                    catalog = JSON.parse(JSON.stringify(INITIAL_CATALOG));
                }
            } else {
                catalog = JSON.parse(JSON.stringify(INITIAL_CATALOG));
            }
            renderAll();
        }

        // Save data to localStorage
        function persistData() {
            localStorage.setItem('tftf_basic_abilities_draft', JSON.stringify(catalog));
        }

        // Hex to char helper
        function hexToChar(hexStr) {
            if (!hexStr) return '';
            try {
                const code = parseInt(hexStr.trim().replace(/^0x/i, ''), 16);
                return code > 0 ? String.fromCharCode(code) : '';
            } catch(e) {
                return '';
            }
        }

        // Render UI
        function renderAll() {
            updateStats();
            renderCategoryFilters();
            renderAbilities();
        }

        function updateStats() {
            document.getElementById('stat-total').textContent = catalog.abilities.length;
            document.getElementById('stat-bots').textContent = catalog.characters_all.length;
            
            const cats = new Set(catalog.abilities.map(a => a.category));
            document.getElementById('stat-cats').textContent = cats.size;
        }

        function renderCategoryFilters() {
            const container = document.getElementById('cat-filters');
            const cats = ['all', ...Array.from(new Set(catalog.abilities.map(a => a.category)))];
            
            container.innerHTML = cats.map(cat => {
                const count = cat === 'all' 
                    ? catalog.abilities.length 
                    : catalog.abilities.filter(a => a.category === cat).length;
                const label = cat === 'all' ? '全部' : cat;
                const activeCls = activeCategory === cat ? 'active' : '';
                return `<span class="cat-pill ${activeCls}" onclick="filterCategory('${cat}')">${label} (${count})</span>`;
            }).join('');
        }

        function filterCategory(cat) {
            activeCategory = cat;
            renderCategoryFilters();
            renderAbilities();
        }

        function handleSearch() {
            searchQuery = document.getElementById('search-input').value.trim().toLowerCase();
            renderAbilities();
        }

        function switchView(view) {
            currentView = view;
            document.getElementById('view-table-btn').classList.toggle('active', view === 'table');
            document.getElementById('view-cards-btn').classList.toggle('active', view === 'cards');
            document.getElementById('table-container').style.display = view === 'table' ? 'block' : 'none';
            document.getElementById('cards-container').style.display = view === 'cards' ? 'grid' : 'none';
        }

        // Filter abilities by category and search query
        function getFilteredAbilities() {
            return catalog.abilities.filter(ab => {
                const matchCat = (activeCategory === 'all' || ab.category === activeCategory);
                if (!matchCat) return false;
                
                if (!searchQuery) return true;
                
                const query = searchQuery;
                const nameMatch = (ab.name_zh && ab.name_zh.toLowerCase().includes(query)) ||
                                  (ab.name_en && ab.name_en.toLowerCase().includes(query));
                const puaMatch = (ab.pua_icon && ab.pua_icon.toLowerCase().includes(query));
                const descMatch = (ab.desc_zh && ab.desc_zh.toLowerCase().includes(query)) ||
                                  (ab.desc_en && ab.desc_en.toLowerCase().includes(query));
                const botMatch = ab.associated_bots && ab.associated_bots.some(b => 
                    (b.name_zh && b.name_zh.toLowerCase().includes(query)) ||
                    (b.bot_id && b.bot_id.toLowerCase().includes(query))
                );

                return nameMatch || puaMatch || descMatch || botMatch;
            });
        }

        function renderAbilities() {
            const list = getFilteredAbilities();
            
            // Render Table
            const tbody = document.getElementById('abilities-table-body');
            if (list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 32px;">未匹配到任何基础能力</td></tr>`;
            } else {
                tbody.innerHTML = list.map(ab => {
                    const iconChar = hexToChar(ab.pua_icon);
                    const botCount = ab.associated_bots ? ab.associated_bots.length : 0;
                    return `
                        <tr>
                            <td>
                                <span class="pua-glyph">${iconChar}</span>
                                <span class="pua-hex-badge">${ab.pua_icon || '无'}</span>
                            </td>
                            <td>
                                <div class="name-cell">
                                    <span class="name-zh">${ab.name_zh}</span>
                                    <span class="name-en">${ab.name_en || ''}</span>
                                </div>
                            </td>
                            <td>
                                <span class="cat-badge cat-${ab.category}">${ab.category}</span>
                            </td>
                            <td>
                                <div class="desc-text">${ab.desc_zh}</div>
                            </td>
                            <td style="text-align: center;">
                                <button class="bot-count-btn" onclick="openBotsModal('${ab.id}')">
                                    🤖 ${botCount} 位英雄
                                </button>
                            </td>
                            <td style="text-align: center;">
                                <button class="btn-secondary" style="padding: 4px 8px; font-size: 12px;" onclick="openEditModal('${ab.id}')">✏️ 编辑</button>
                                <button class="btn-secondary" style="padding: 4px 8px; font-size: 12px; color: #EF4444;" onclick="deleteAbility('${ab.id}')">🗑️</button>
                            </td>
                        </tr>
                    `;
                }).join('');
            }

            // Render Cards
            const cardsGrid = document.getElementById('cards-container');
            if (list.length === 0) {
                cardsGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 32px;">未匹配到任何基础能力</div>`;
            } else {
                cardsGrid.innerHTML = list.map(ab => {
                    const iconChar = hexToChar(ab.pua_icon);
                    const botCount = ab.associated_bots ? ab.associated_bots.length : 0;
                    return `
                        <div class="ability-card">
                            <div class="card-header">
                                <div class="card-icon-box">${iconChar}</div>
                                <div class="card-title-group">
                                    <h3>${ab.name_zh} <span class="pua-hex-badge">${ab.pua_icon || '无'}</span></h3>
                                    <span class="sub">${ab.name_en || ''}</span>
                                </div>
                                <span class="cat-badge cat-${ab.category}">${ab.category}</span>
                            </div>
                            <div class="card-body">
                                ${ab.desc_zh}
                            </div>
                            <div class="card-footer">
                                <button class="bot-count-btn" onclick="openBotsModal('${ab.id}')">
                                    🤖 ${botCount} 位英雄
                                </button>
                                <div style="display: flex; gap: 6px;">
                                    <button class="btn-secondary" style="padding: 4px 8px; font-size: 12px;" onclick="openEditModal('${ab.id}')">编辑</button>
                                    <button class="btn-secondary" style="padding: 4px 8px; font-size: 12px; color: #EF4444;" onclick="deleteAbility('${ab.id}')">删除</button>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');
            }
        }

        // Edit / Add Modal Handlers
        function openEditModal(id) {
            editingAbilityId = id;
            const ab = catalog.abilities.find(a => a.id === id);
            if (!ab) return;

            document.getElementById('modal-title').textContent = `编辑基础能力: ${ab.name_zh}`;
            document.getElementById('edit-id').value = ab.id;
            document.getElementById('edit-name-zh').value = ab.name_zh || '';
            document.getElementById('edit-name-en').value = ab.name_en || '';
            document.getElementById('edit-category').value = ab.category || '持续伤害';
            document.getElementById('edit-pua-icon').value = ab.pua_icon || '';
            document.getElementById('edit-desc-zh').value = ab.desc_zh || '';
            document.getElementById('edit-desc-en').value = ab.desc_en || '';

            updateModalIconPreview();
            document.getElementById('edit-modal').classList.add('active');
        }

        function openAddModal() {
            editingAbilityId = null;
            document.getElementById('modal-title').textContent = '新增共性基础能力';
            document.getElementById('edit-id').value = '';
            document.getElementById('edit-name-zh').value = '';
            document.getElementById('edit-name-en').value = '';
            document.getElementById('edit-category').value = '持续伤害';
            document.getElementById('edit-pua-icon').value = '';
            document.getElementById('edit-desc-zh').value = '';
            document.getElementById('edit-desc-en').value = '';

            updateModalIconPreview();
            document.getElementById('edit-modal').classList.add('active');
        }

        function closeEditModal() {
            document.getElementById('edit-modal').classList.remove('active');
        }

        function selectQuickIcon(hex) {
            document.getElementById('edit-pua-icon').value = hex;
            updateModalIconPreview();
        }

        function updateModalIconPreview() {
            const hex = document.getElementById('edit-pua-icon').value.trim();
            document.getElementById('modal-icon-preview').textContent = hexToChar(hex);
        }

        function saveAbilityModal() {
            const nameZh = document.getElementById('edit-name-zh').value.trim();
            if (!nameZh) {
                alert('请输入中文能力名称');
                return;
            }

            const puaHex = document.getElementById('edit-pua-icon').value.trim().toUpperCase();
            const descZh = document.getElementById('edit-desc-zh').value.trim();

            if (editingAbilityId) {
                // Update existing
                const ab = catalog.abilities.find(a => a.id === editingAbilityId);
                if (ab) {
                    ab.name_zh = nameZh;
                    ab.name_en = document.getElementById('edit-name-en').value.trim();
                    ab.category = document.getElementById('edit-category').value;
                    ab.pua_icon = puaHex;
                    ab.pua_char = hexToChar(puaHex);
                    ab.desc_zh = descZh;
                    ab.desc_en = document.getElementById('edit-desc-en').value.trim();
                }
            } else {
                // Add new
                const newId = 'ability_' + Date.now();
                catalog.abilities.unshift({
                    id: newId,
                    name_zh: nameZh,
                    name_en: document.getElementById('edit-name-en').value.trim(),
                    category: document.getElementById('edit-category').value,
                    pua_icon: puaHex,
                    pua_char: hexToChar(puaHex),
                    desc_zh: descZh,
                    desc_en: document.getElementById('edit-desc-en').value.trim(),
                    associated_bots: []
                });
            }

            persistData();
            closeEditModal();
            renderAll();
            showToast('已成功保存修改！');
        }

        function deleteAbility(id) {
            const ab = catalog.abilities.find(a => a.id === id);
            if (!ab) return;
            if (confirm(`确定要删除基础能力【${ab.name_zh}】吗？`)) {
                catalog.abilities = catalog.abilities.filter(a => a.id !== id);
                persistData();
                renderAll();
                showToast('已删除能力项');
            }
        }

        // Bot Association Modal Handlers
        function openBotsModal(id) {
            managingBotsAbilityId = id;
            const ab = catalog.abilities.find(a => a.id === id);
            if (!ab) return;

            document.getElementById('bots-modal-title').textContent = `为【${ab.name_zh}】配置关联英雄`;
            tempSelectedBots = new Set(ab.associated_bots ? ab.associated_bots.map(b => b.bot_id) : []);
            
            document.getElementById('modal-bot-search').value = '';
            renderModalBots();
            document.getElementById('bots-modal').classList.add('active');
        }

        function closeBotsModal() {
            document.getElementById('bots-modal').classList.remove('active');
        }

        function renderModalBots() {
            const query = (document.getElementById('modal-bot-search').value || '').trim().toLowerCase();
            const container = document.getElementById('modal-bot-pills');
            
            const bots = catalog.characters_all.filter(b => {
                if (!query) return true;
                return (b.name_zh && b.name_zh.toLowerCase().includes(query)) ||
                       (b.bot_id && b.bot_id.toLowerCase().includes(query)) ||
                       (b.faction && b.faction.toLowerCase().includes(query)) ||
                       (b.class && b.class.toLowerCase().includes(query));
            });

            container.innerHTML = bots.map(b => {
                const isSelected = tempSelectedBots.has(b.id || b.bot_id);
                const bid = b.id || b.bot_id;
                return `
                    <div class="bot-check-label ${isSelected ? 'selected' : ''}" onclick="toggleBotSelect('${bid}')">
                        <input type="checkbox" ${isSelected ? 'checked' : ''} onclick="event.stopPropagation(); toggleBotSelect('${bid}')">
                        <span>${b.name_zh}</span>
                        <span style="font-size: 10px; color: var(--text-sub);">[${b.class || ''}]</span>
                    </div>
                `;
            }).join('');
        }

        function toggleBotSelect(bid) {
            if (tempSelectedBots.has(bid)) {
                tempSelectedBots.delete(bid);
            } else {
                tempSelectedBots.add(bid);
            }
            renderModalBots();
        }

        function filterModalBots() {
            renderModalBots();
        }

        function toggleSelectAllBots(selectAll) {
            if (selectAll) {
                catalog.characters_all.forEach(b => tempSelectedBots.add(b.id || b.bot_id));
            } else {
                tempSelectedBots.clear();
            }
            renderModalBots();
        }

        function saveBotsModal() {
            const ab = catalog.abilities.find(a => a.id === managingBotsAbilityId);
            if (!ab) return;

            ab.associated_bots = catalog.characters_all.filter(b => tempSelectedBots.has(b.id || b.bot_id)).map(b => ({
                bot_id: b.id || b.bot_id,
                name_zh: b.name_zh,
                name_en: b.name_en,
                faction: b.faction,
                class: b.class
            }));

            persistData();
            closeBotsModal();
            renderAll();
            showToast(`已更新【${ab.name_zh}】关联角色 (${ab.associated_bots.length} 位)`);
        }

        // Export JSON
        function exportJSON() {
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(catalog, null, 2));
            const dlAnchor = document.createElement('a');
            dlAnchor.setAttribute("href", dataStr);
            dlAnchor.setAttribute("download", "basic_abilities.json");
            document.body.appendChild(dlAnchor);
            dlAnchor.click();
            dlAnchor.remove();
            showToast('已导出 basic_abilities.json 文件！');
        }

        // Copy JSON
        function copyFullJSON() {
            const jsonText = JSON.stringify(catalog, null, 2);
            navigator.clipboard.writeText(jsonText).then(() => {
                showToast('已复制完整 JSON 内容到剪贴板！');
            }).catch(err => {
                alert('复制失败，请手动导出 JSON 文件');
            });
        }

        // Import JSON
        document.getElementById('import-file-input').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(evt) {
                try {
                    const imported = JSON.parse(evt.target.result);
                    if (imported.abilities && Array.isArray(imported.abilities)) {
                        catalog = imported;
                        persistData();
                        renderAll();
                        showToast(`已成功导入 ${catalog.abilities.length} 项基础能力！`);
                    } else {
                        alert('JSON 格式错误：缺少 abilities 数组');
                    }
                } catch(err) {
                    alert('导入失败：无效的 JSON 文件格式');
                }
            };
            reader.readAsText(file, 'utf-8');
            e.target.value = '';
        });

        // Reset
        function resetToDefault() {
            if (confirm('确定要恢复为系统默认初始数据吗？本地所有未导出的修改将被覆盖。')) {
                localStorage.removeItem('tftf_basic_abilities_draft');
                catalog = JSON.parse(JSON.stringify(INITIAL_CATALOG));
                renderAll();
                showToast('已恢复为官方提取基线默认数据');
            }
        }

        // Toast
        function showToast(msg) {
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.style.display = 'block';
            setTimeout(() => {
                t.style.display = 'none';
            }, 3000);
        }

        // Start
        window.addEventListener('DOMContentLoaded', initData);
    </script>
</body>
</html>
"""

out_html_path = Path("tools/web_dashboard/basic_abilities_editor.html")
with open(out_html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Generated {out_html_path} successfully! Size: {out_html_path.stat().st_size} bytes")
