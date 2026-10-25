// TFTF Combat Simulator Client Application

let isRunning = false;
let tickTimer = null;
let currentInjectTarget = 0; // 0=P0, 1=P1
let p0Blocking = false;

// DOM Elements
const timerDisplay = document.getElementById("timerDisplay");
const stageTimerDisplay = document.getElementById("stageTimerDisplay");
const btnPlay = document.getElementById("btnPlay");
const btnPause = document.getElementById("btnPause");
const btnStop = document.getElementById("btnStop");
const btnStep = document.getElementById("btnStep");
const btnReset = document.getElementById("btnReset");
const btnRecompile = document.getElementById("btnRecompile");
const announcementText = document.getElementById("announcementText");
const stageCenterAnnoText = document.getElementById("stageCenterAnnoText");

const p0BotSelect = document.getElementById("p0BotSelect");
const p1BotSelect = document.getElementById("p1BotSelect");
const p0Name = document.getElementById("p0Name");
const p1Name = document.getElementById("p1Name");
const stageP0Name = document.getElementById("stageP0Name");
const stageP1Name = document.getElementById("stageP1Name");
const p0BotId = document.getElementById("p0BotId");
const p1BotId = document.getElementById("p1BotId");
const p0HpText = document.getElementById("p0HpText");
const p1HpText = document.getElementById("p1HpText");
const stageP0HpText = document.getElementById("stageP0HpText");
const stageP1HpText = document.getElementById("stageP1HpText");
const p0HpFill = document.getElementById("p0HpFill");
const p1HpFill = document.getElementById("p1HpFill");
const stageP0HpFill = document.getElementById("stageP0HpFill");
const stageP1HpFill = document.getElementById("stageP1HpFill");
const p0ManaText = document.getElementById("p0ManaText");
const p1ManaText = document.getElementById("p1ManaText");
const p0ManaFill = document.getElementById("p0ManaFill");
const p1ManaFill = document.getElementById("p1ManaFill");
const p0BuffTray = document.getElementById("p0BuffTray");
const p1BuffTray = document.getElementById("p1BuffTray");

// 擂台主视区能量段与机甲角色
const p0ManaSeg1 = document.getElementById("p0ManaSeg1");
const p0ManaSeg2 = document.getElementById("p0ManaSeg2");
const p0ManaSeg3 = document.getElementById("p0ManaSeg3");
const p1ManaSeg1 = document.getElementById("p1ManaSeg1");
const p1ManaSeg2 = document.getElementById("p1ManaSeg2");
const p1ManaSeg3 = document.getElementById("p1ManaSeg3");

const fighterP0 = document.getElementById("fighterP0");
const fighterP1 = document.getElementById("fighterP1");
const shieldP0 = document.getElementById("shieldP0");
const shieldP1 = document.getElementById("shieldP1");

const floaterContainer = document.getElementById("floaterContainer");
const logTerminal = document.getElementById("logTerminal");
const btnClearLogs = document.getElementById("btnClearLogs");

const btnSP1 = document.getElementById("btnSP1");
const btnSP2 = document.getElementById("btnSP2");
const btnSP3 = document.getElementById("btnSP3");
const btnToggleBlock = document.getElementById("btnToggleBlock");
const btnDashBack = document.getElementById("btnDashBack");
const btnSidestep = document.getElementById("btnSidestep");
const btnCombo5 = document.getElementById("btnCombo5");

// Modal Elements
const injectModal = document.getElementById("injectModal");
const modalTitle = document.getElementById("modalTitle");
const modalBuffSelect = document.getElementById("modalBuffSelect");
const customBuffGroup = document.getElementById("customBuffGroup");
const modalCustomBuffId = document.getElementById("modalCustomBuffId");
const modalBuffDur = document.getElementById("modalBuffDur");
const modalBuffStacks = document.getElementById("modalBuffStacks");
const btnModalClose = document.getElementById("btnModalClose");
const btnModalCancel = document.getElementById("btnModalCancel");
const btnModalApply = document.getElementById("btnModalApply");

// ---------------------------------------------------------------------------
// 初始化与数据加载
// ---------------------------------------------------------------------------
async function init() {
    await loadBots();
    setupEventHandlers();
    fetchState();
}

let g_allBots = [];
let g_botSortMode = localStorage.getItem("tftf_bot_sort_mode") || "class";

// TFTF 官方六边形克制环 (左上斗士紫，逆时针: 战术蓝、爆破黄、科技青蓝、侦查绿、战士红)
const CLASS_CONFIG = {
    braw: { id: "braw", name_zh: "斗士系", name_en: "Brawler",    icon: "✊", color: "#9B45E4" },
    tact: { id: "tact", name_zh: "战术系", name_en: "Tactician",  icon: "♞", color: "#2F6DF2" },
    demo: { id: "demo", name_zh: "爆破系", name_en: "Demolition", icon: "💥", color: "#F2B800" },
    tech: { id: "tech", name_zh: "科技系", name_en: "Tech",       icon: "💠", color: "#00B8DA" },
    scou: { id: "scou", name_zh: "侦查系", name_en: "Scout",      icon: "🪽", color: "#22C55E" },
    warr: { id: "warr", name_zh: "战士系", name_en: "Warrior",    icon: "⚔️", color: "#E82B25" },
};

const CLASS_ORDER = ["braw", "tact", "demo", "tech", "scou", "warr"];

function populateBotSelect(selectEl, selectedBotId) {
    if (!selectEl || !g_allBots.length) return;
    const currentVal = selectedBotId || selectEl.value;
    selectEl.innerHTML = "";

    if (g_botSortMode === "class") {
        CLASS_ORDER.forEach(cid => {
            const conf = CLASS_CONFIG[cid];
            const classBots = g_allBots.filter(b => b.class === cid);
            if (!classBots.length) return;

            // 类别内部按中文首字拼音序排
            classBots.sort((a, b) => a.name_zh.localeCompare(b.name_zh, "zh-Hans-CN"));

            const grp = document.createElement("optgroup");
            grp.label = `${conf.icon} ${conf.name_zh} (${conf.name_en}) · ${classBots.length}人`;
            grp.className = `group-${cid}`;

            classBots.forEach(b => {
                const opt = document.createElement("option");
                opt.value = b.bot_id;
                opt.className = `bot-opt bot-opt-${cid}`;
                opt.style.color = conf.color;
                opt.style.backgroundColor = "#0d1117";
                opt.textContent = `${b.name_zh} (${b.name_en})`;
                if (b.bot_id === currentVal) opt.selected = true;
                grp.appendChild(opt);
            });
            selectEl.appendChild(grp);
        });
    } else if (g_botSortMode === "pinyin") {
        const sorted = [...g_allBots].sort((a, b) => a.name_zh.localeCompare(b.name_zh, "zh-Hans-CN"));
        sorted.forEach(b => {
            const conf = CLASS_CONFIG[b.class] || { color: "#c9d1d9" };
            const opt = document.createElement("option");
            opt.value = b.bot_id;
            opt.className = `bot-opt bot-opt-${b.class}`;
            opt.style.color = conf.color;
            opt.style.backgroundColor = "#0d1117";
            opt.textContent = `${b.name_zh} (${b.name_en})`;
            if (b.bot_id === currentVal) opt.selected = true;
            selectEl.appendChild(opt);
        });
    } else if (g_botSortMode === "en") {
        const sorted = [...g_allBots].sort((a, b) => (a.name_en || "").localeCompare(b.name_en || ""));
        sorted.forEach(b => {
            const conf = CLASS_CONFIG[b.class] || { color: "#c9d1d9" };
            const opt = document.createElement("option");
            opt.value = b.bot_id;
            opt.className = `bot-opt bot-opt-${b.class}`;
            opt.style.color = conf.color;
            opt.style.backgroundColor = "#0d1117";
            opt.textContent = `${b.name_zh} (${b.name_en})`;
            if (b.bot_id === currentVal) opt.selected = true;
            selectEl.appendChild(opt);
        });
    }

    if (!selectEl.value && selectEl.options.length > 0) {
        selectEl.selectedIndex = 0;
    }
    updateSelectClassColor(selectEl);
}

function updateSelectClassColor(selectEl) {
    if (!selectEl) return;
    const botId = selectEl.value;
    const b = g_allBots.find(x => x.bot_id === botId);
    if (b && CLASS_CONFIG[b.class]) {
        const conf = CLASS_CONFIG[b.class];
        selectEl.style.color = conf.color;
        selectEl.style.borderColor = `${conf.color}99`;
        selectEl.style.boxShadow = `0 0 6px ${conf.color}33`;
    } else {
        selectEl.style.color = "#c9d1d9";
        selectEl.style.borderColor = "#30363d";
        selectEl.style.boxShadow = "none";
    }
}

function renderBots() {
    const val0 = p0BotSelect.value || "optimusprime_cin_tf";
    const val1 = p1BotSelect.value || "bonecrusher_cin_rotf";
    populateBotSelect(p0BotSelect, val0);
    populateBotSelect(p1BotSelect, val1);

    if (p0BotSelect.selectedIndex >= 0) {
        const t0 = p0BotSelect.options[p0BotSelect.selectedIndex].text.split(" (")[0];
        if (p0Name) p0Name.textContent = t0;
        if (stageP0Name) stageP0Name.textContent = t0;
    }
    if (p1BotSelect.selectedIndex >= 0) {
        const t1 = p1BotSelect.options[p1BotSelect.selectedIndex].text.split(" (")[0];
        if (p1Name) p1Name.textContent = t1;
        if (stageP1Name) stageP1Name.textContent = t1;
    }
}

async function loadBots() {
    try {
        const res = await fetch("/api/bots");
        g_allBots = await res.json();
        renderBots();
    } catch (e) {
        console.error("Failed to load bots:", e);
    }
}

// ---------------------------------------------------------------------------
// 状态轮询与渲染
// ---------------------------------------------------------------------------
async function fetchState() {
    try {
        const res = await fetch("/api/state");
        const data = await res.json();
        renderState(data);
    } catch (e) {
        console.error("fetchState error:", e);
    }
}

function renderState(data) {
    if (!data || !data.p0) return;

    // 1. 时钟格式化 (ms -> mm:ss.ms)
    const ms = data.clock_ms || 0;
    const totalSec = Math.floor(ms / 1000);
    const m = String(Math.floor(totalSec / 60)).padStart(2, "0");
    const s = String(totalSec % 60).padStart(2, "0");
    const remMs = String(ms % 1000).padStart(3, "0");
    const formattedTime = `${m}:${s}.${remMs}`;
    timerDisplay.textContent = formattedTime;
    if (stageTimerDisplay) stageTimerDisplay.textContent = formattedTime;

    // 2. 广播条与中央擂台通知横幅
    if (data.announcement) {
        announcementText.textContent = data.announcement;
        if (stageCenterAnnoText) stageCenterAnnoText.textContent = `⚡ ${data.announcement}`;
    }

    // 3. 护盾与格挡状态联动
    if (shieldP0) shieldP0.classList.toggle("active", !!data.p0.is_blocking);
    if (shieldP1) shieldP1.classList.toggle("active", !!data.p1.is_blocking);

    // 4. 1P 与 2P 状态
    renderPlayer(0, data.p0);
    renderPlayer(1, data.p1);

    // 5. SP 按钮不受能量限制：无界沙盒模式，无论能量多少均可强行释放特技
    btnSP1.disabled = false;
    btnSP2.disabled = false;
    btnSP3.disabled = false;
    btnSP1.style.opacity = "1";
    btnSP2.style.opacity = "1";
    btnSP3.style.opacity = "1";

    // 6. 渲染战斗浮字 (Floaters)
    if (data.floaters && data.floaters.length > 0) {
        data.floaters.forEach(spawnFloater);
    }

    // 7. 渲染日志 (Logs)
    if (data.logs && data.logs.length > 0) {
        data.logs.forEach(appendLog);
    }
}

// PUA 图标与状态类型识别解析
function getBuffPuaInfo(buffId) {
    const id = buffId.toLowerCase();
    let pua = 0xE406;
    let typeClass = "is-buff";
    let name = buffId;

    if (id.includes("bleed")) {
        pua = 0xE401; // 流血
        typeClass = "is-debuff is-bleed";
        name = "流血 (Bleed)";
    } else if (id.includes("burn") || id.includes("flame") || id.includes("fire")) {
        pua = 0xE41D; // 灼烧
        typeClass = "is-debuff is-burn";
        name = "灼烧 (Burn)";
    } else if (id.includes("shock") || id.includes("elect")) {
        pua = 0xE914; // 震击
        typeClass = "is-debuff is-shock";
        name = "震击 (Shock)";
    } else if (id.includes("armor_break") || id.includes("break")) {
        pua = 0xE516; // 破甲
        typeClass = "is-debuff";
        name = "破甲 (Armor Break)";
    } else if (id.includes("armor") || id.includes("shield")) {
        pua = 0xE517; // 护甲
        typeClass = "is-buff";
        name = "护甲 (Armor)";
    } else if (id.includes("melee")) {
        pua = 0xE412; // 近战增益
        typeClass = "is-buff";
        name = "近战增益 (Melee)";
    } else if (id.includes("willpower")) {
        pua = 0xE942; // 意志力
        typeClass = "is-buff is-heal";
        name = "意志力 (Willpower)";
    } else if (id.includes("purify")) {
        pua = 0xE942; // 意志力/净化 (Willpower/Purify)
        typeClass = "is-buff is-heal";
        name = "净化 (Purify)";
    } else if (id.includes("crit")) {
        pua = 0xE40D; // 暴击
        typeClass = "is-buff is-crit";
        name = "暴击增益 (Crit)";
    } else if (id.includes("evade") || id.includes("dodge")) {
        pua = 0xE509; // 闪避
        typeClass = "is-buff";
        name = "闪避/规避 (Evade)";
    } else if (id.includes("stun")) {
        pua = 0xE605; // 眩晕
        typeClass = "is-debuff";
        name = "眩晕 (Stun)";
    } else if (id.includes("decel")) {
        pua = 0xE952; // 减速
        typeClass = "is-debuff";
        name = "时间减速 (Decel)";
    } else if (id.includes("unstoppable")) {
        pua = 0xE915; // 霸体
        typeClass = "is-buff";
        name = "不可阻挡 (Unstoppable)";
    }

    return {
        char: String.fromCharCode(pua),
        hex: "0x" + pua.toString(16).toUpperCase(),
        typeClass,
        name
    };
}

function updateManaSegments(isP0, mana) {
    const seg1 = isP0 ? p0ManaSeg1 : p1ManaSeg1;
    const seg2 = isP0 ? p0ManaSeg2 : p1ManaSeg2;
    const seg3 = isP0 ? p0ManaSeg3 : p1ManaSeg3;
    const manaNumEl = isP0 ? document.getElementById("stageP0ManaNum") : document.getElementById("stageP1ManaNum");
    const spHexBtn = isP0 ? document.getElementById("stageP0SpHexBtn") : document.getElementById("stageP1SpHexBtn");
    const spTextEl = isP0 ? document.getElementById("stageP0SpText") : document.getElementById("stageP1SpText");

    if (manaNumEl) {
        manaNumEl.textContent = `${mana.toFixed(2)} / 3.00 (${Math.round((mana / 3.0) * 100)}%)`;
    }

    if (seg1 && seg2 && seg3) {
        // 段1 (0.0 ~ 1.0)
        const fill1 = seg1.querySelector(".seg-fill");
        const p1 = Math.min(100, Math.max(0, mana * 100));
        fill1.style.width = `${p1}%`;
        seg1.classList.toggle("is-full", mana >= 1.0);

        // 段2 (1.0 ~ 2.0)
        const fill2 = seg2.querySelector(".seg-fill");
        const p2 = Math.min(100, Math.max(0, (mana - 1.0) * 100));
        fill2.style.width = `${p2}%`;
        seg2.classList.toggle("is-full", mana >= 2.0);

        // 段3 (2.0 ~ 3.0)
        const fill3 = seg3.querySelector(".seg-fill");
        const p3 = Math.min(100, Math.max(0, (mana - 2.0) * 100));
        fill3.style.width = `${p3}%`;
        seg3.classList.toggle("is-full", mana >= 3.0);
    }

    // SP 六边形按键状态联动
    if (spHexBtn && spTextEl) {
        spHexBtn.classList.remove("can-sp1", "can-sp2", "can-sp3");
        if (mana >= 3.0) {
            spHexBtn.classList.add("can-sp3");
            spTextEl.textContent = "SP3";
        } else if (mana >= 2.0) {
            spHexBtn.classList.add("can-sp2");
            spTextEl.textContent = "SP2";
        } else if (mana >= 1.0) {
            spHexBtn.classList.add("can-sp1");
            spTextEl.textContent = "SP1";
        } else {
            spTextEl.textContent = "SP";
        }
    }
}

function renderPlayer(idx, p) {
    const isP0 = (idx === 0);
    const nameEl = isP0 ? p0Name : p1Name;
    const stageNameEl = isP0 ? stageP0Name : stageP1Name;
    const botIdEl = isP0 ? p0BotId : p1BotId;
    const hpTextEl = isP0 ? p0HpText : p1HpText;
    const stageHpTextEl = isP0 ? stageP0HpText : stageP1HpText;
    const hpFillEl = isP0 ? p0HpFill : p1HpFill;
    const stageHpFillEl = isP0 ? stageP0HpFill : stageP1HpFill;
    const manaTextEl = isP0 ? p0ManaText : p1ManaText;
    const manaFillEl = isP0 ? p0ManaFill : p1ManaFill;
    const buffTrayEl = isP0 ? p0BuffTray : p1BuffTray;

    botIdEl.textContent = p.bot_id;

    // HP 百分比
    const hpPct = Math.max(0, Math.min(100, (p.hp / p.max_hp) * 100));
    if (hpFillEl) hpFillEl.style.width = `${hpPct}%`;
    if (stageHpFillEl) stageHpFillEl.style.width = `${hpPct}%`;
    const hpFormatted = `${Math.round(p.hp)} / ${Math.round(p.max_hp)}`;
    if (hpTextEl) hpTextEl.textContent = hpFormatted;
    if (stageHpTextEl) stageHpTextEl.textContent = hpFormatted;

    // Mana 能量段更新
    updateManaSegments(isP0, p.mana);

    // 1. 渲染血条下方的 PUA 环形倒计时圈 (DOM 差量复用更新，杜绝每100ms重建导致的狂闪)
    const buffRingsEl = isP0 ? document.getElementById("stageP0BuffRings") : document.getElementById("stageP1BuffRings");
    renderBuffRingsDOM(buffRingsEl, p.buffs, idx);

    // 2. 侧边栏 Buff 列表渲染
    if (!p.buffs || p.buffs.length === 0) {
        buffTrayEl.innerHTML = '<span class="buff-empty">暂无状态</span>';
    } else {
        buffTrayEl.innerHTML = "";
        p.buffs.forEach(b => {
            const badge = document.createElement("div");
            const isPerm = (b.rem_ms < 0);
            const isValid = (b.is_contract_valid !== false);
            badge.className = `buff-badge ${isPerm ? "is-perm" : ""} ${!isValid ? "is-contract-invalid" : ""}`;

            const info = getBuffPuaInfo(b.id);
            const puaChar = b.pua_char || info.char;
            const displayName = b.name || info.name || b.id;
            const timeStr = isPerm ? "永久" : `${(b.rem_ms / 1000).toFixed(1)}s`;
            const stackStr = (b.stacks > 1) ? ` x${b.stacks}` : "";
            const colorStyle = b.tc ? `color:#${b.tc};` : "";
            const warnIcon = !isValid ? `<span title="${b.contract_warning || '未在官方能力库注册'}" style="color:#ef4444;margin-left:4px;">⚠️</span>` : "";

            badge.innerHTML = `
                <span class="tecnica-icon" style="margin-right:4px;font-size:14px;${colorStyle}">${puaChar}</span>
                <span><strong style="${colorStyle}">${displayName}</strong>${stackStr} [${timeStr}]${warnIcon}</span>
                <span class="b-close" title="驱散此Buff" onclick="removeBuff(${idx}, '${b.id}')">&times;</span>
            `;
            buffTrayEl.appendChild(badge);
        });
    }
}

// ---------------------------------------------------------------------------
// 战斗浮字与错峰分流系统 (Anti-Overlap Staggered Floater Manager)
// ---------------------------------------------------------------------------
const floaterStacks = {
    0: { lastTime: 0, level: 0 },
    1: { lastTime: 0, level: 0 }
};

function spawnFloater(f) {
    const el = document.createElement("div");
    const pidx = (f.pidx === 1) ? 1 : 0;
    el.className = `floater floater-p${pidx}`;

    let typeClass = "floater-dmg";
    let prefix = "-";
    if (f.type === 1) { 
        typeClass = "floater-crit"; 
        prefix = "⚡ 暴击 -"; 
    } else if (f.type === 2) { 
        typeClass = "floater-heal"; 
        prefix = "💚 +"; 
    } else if (f.type === 3) { 
        typeClass = "floater-mana"; 
        prefix = "⚡ +"; 
    } else if (f.type === 4 || f.type === 5) { 
        typeClass = "floater-text"; 
        prefix = ""; 
    }

    el.classList.add(typeClass);
    const valText = f.val > 0 ? Math.round(f.val) : "";
    el.textContent = `${prefix}${valText} ${f.text || ""}`;

    // 受击战士轻微晃动
    const victim = (pidx === 0) ? fighterP0 : fighterP1;
    if (victim && (f.type === 0 || f.type === 1)) {
        victim.classList.remove("hit-react");
        void victim.offsetWidth;
        victim.classList.add("hit-react");
        setTimeout(() => victim.classList.remove("hit-react"), 220);
    }

    // -----------------------------------------------------------------------
    // 高度与横向错峰分流算法 (保证字与字垂直重叠 <= 0~15%，充分利用上方开阔空间)
    // -----------------------------------------------------------------------
    const now = performance.now();
    const tracker = floaterStacks[pidx];
    if (now - tracker.lastTime < 800) {
        tracker.level = (tracker.level + 1) % 6; // 在 0 到 5 阶高度中错峰排布
    } else {
        tracker.level = 0;
    }
    tracker.lastTime = now;

    // 垂直错峰高度：每阶拉开 36px (字号约 19px，间距 36px 确保垂直 0% 重合)
    const yOffset = tracker.level * 36;

    // 水平横向散射：交替向左向右展开 (0, +35px, -35px, +70px, -70px, +105px)
    const sign = (tracker.level % 2 === 1) ? 1 : -1;
    const mag = Math.ceil(tracker.level / 2) * 36;
    const xOffset = tracker.level === 0 ? 0 : sign * mag;

    el.style.setProperty("--spawn-x", `${xOffset}px`);
    el.style.setProperty("--spawn-y", `${yOffset}px`);

    floaterContainer.appendChild(el);
    setTimeout(() => el.remove(), 1400);
}

function appendLog(line) {
    const p = document.createElement("div");
    p.className = "log-line";
    if (line.includes("ROLL_DICE_PASS")) {
        p.classList.add("log-dice-pass");
    } else if (line.includes("ROLL_DICE_FAIL")) {
        p.classList.add("log-dice-fail");
    } else if (line.includes("OPTIMUS_MV") || line.includes("MEGATRON") || line.includes("PROWL") || line.includes("WINDBLADE") || line.includes("BONECRUSHER")) {
        p.classList.add("log-skill");
    } else if (line.includes("HIT") || line.includes("ATTACK")) {
        p.classList.add("log-hit");
    } else {
        p.classList.add("log-sim");
    }
    p.textContent = `[LOG] ${line}`;
    logTerminal.appendChild(p);
    logTerminal.scrollTop = logTerminal.scrollHeight;
}

// ---------------------------------------------------------------------------
// 交互事件处理
// ---------------------------------------------------------------------------
function setupEventHandlers() {
    // 角色名字点击 -> 弹出已实装技能列表弹窗
    const p0NameEl = document.getElementById("p0Name");
    const p1NameEl = document.getElementById("p1Name");
    const stageP0NameEl = document.getElementById("stageP0Name");
    const stageP1NameEl = document.getElementById("stageP1Name");

    if (p0NameEl) p0NameEl.addEventListener("click", () => openAbilityModal(p0BotSelect.value));
    if (p1NameEl) p1NameEl.addEventListener("click", () => openAbilityModal(p1BotSelect.value));
    if (stageP0NameEl) stageP0NameEl.addEventListener("click", () => openAbilityModal(p0BotSelect.value));
    if (stageP1NameEl) stageP1NameEl.addEventListener("click", () => openAbilityModal(p1BotSelect.value));

    // 技能弹窗关闭与 Tab 切换
    const btnAbClose = document.getElementById("btnAbilityModalClose");
    const btnAbClose2 = document.getElementById("btnAbilityModalClose2");
    const abModal = document.getElementById("abilityModal");
    if (btnAbClose) btnAbClose.addEventListener("click", closeAbilityModal);
    if (btnAbClose2) btnAbClose2.addEventListener("click", closeAbilityModal);
    if (abModal) {
        abModal.addEventListener("click", (e) => {
            if (e.target === abModal) closeAbilityModal();
        });
    }

    const tabBtnImplemented = document.getElementById("tabBtnImplemented");
    const tabBtnAll = document.getElementById("tabBtnAll");
    const panelImplemented = document.getElementById("panelImplemented");
    const panelAll = document.getElementById("panelAll");

    if (tabBtnImplemented && tabBtnAll) {
        tabBtnImplemented.addEventListener("click", () => {
            tabBtnImplemented.classList.add("active");
            tabBtnAll.classList.remove("active");
            panelImplemented.style.display = "block";
            panelAll.style.display = "none";
        });
        tabBtnAll.addEventListener("click", () => {
            tabBtnAll.classList.add("active");
            tabBtnImplemented.classList.remove("active");
            panelAll.style.display = "block";
            panelImplemented.style.display = "none";
        });
    }

    // 底部六边形 SP 必杀按键点击出招
    const stageP0SpHexBtn = document.getElementById("stageP0SpHexBtn");
    if (stageP0SpHexBtn) {
        stageP0SpHexBtn.addEventListener("click", () => {
            if (stageP0SpHexBtn.classList.contains("can-sp3")) btnSP3.click();
            else if (stageP0SpHexBtn.classList.contains("can-sp2")) btnSP2.click();
            else btnSP1.click(); // 无能量时强行释放 SP1
        });
    }
    // 时钟控制
    btnPlay.addEventListener("click", () => {
        if (!isRunning) {
            isRunning = true;
            btnPlay.textContent = "▶ 运行中...";
            btnPlay.style.background = "#2ea043";
            tickTimer = setInterval(async () => {
                await fetch("/api/tick", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ dt_ms: 100 })
                });
                fetchState();
            }, 100);
        }
    });

    btnPause.addEventListener("click", () => {
        if (isRunning) {
            isRunning = false;
            clearInterval(tickTimer);
            btnPlay.textContent = "▶ 开始模拟";
            btnPlay.style.background = "#238636";
        }
    });

    if (btnStop) {
        btnStop.addEventListener("click", async () => {
            if (isRunning) {
                isRunning = false;
                clearInterval(tickTimer);
                btnPlay.textContent = "▶ 开始模拟";
                btnPlay.style.background = "#238636";
            }
            await fetch("/api/reset", { method: "POST" });
            fetchState();
            showToast("⏹ 模拟已停止并归零重置");
        });
    }

    btnStep.addEventListener("click", async () => {
        await fetch("/api/tick", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ dt_ms: 100 })
        });
        fetchState();
    });

    btnReset.addEventListener("click", async () => {
        await fetch("/api/reset", { method: "POST" });
        fetchState();
        showToast("战斗已重置");
    });

    // 代码热重载 (0.3s 重新编译)
    btnRecompile.addEventListener("click", async () => {
        btnRecompile.textContent = "⏳ 正在重编...";
        try {
            const res = await fetch("/api/recompile", { method: "POST" });
            const data = await res.json();
            if (data.ok) {
                showToast("⚡ 技能代码热重载成功 (0.3s)！");
            } else {
                alert("编译失败:\n" + data.message);
            }
        } catch (e) {
            alert("热重载通信异常: " + e);
        } finally {
            btnRecompile.textContent = "⚡ 热重载技能代码";
            fetchState();
        }
    });

    // 排序模式切换
    const sortSelect = document.getElementById("botSortModeSelect");
    if (sortSelect) {
        sortSelect.value = g_botSortMode;
        sortSelect.addEventListener("change", (e) => {
            g_botSortMode = e.target.value;
            localStorage.setItem("tftf_bot_sort_mode", g_botSortMode);
            renderBots();
        });
    }

    // 角色下拉选择
    p0BotSelect.addEventListener("change", () => {
        updateSelectClassColor(p0BotSelect);
        applyBotMatchup();
    });
    p1BotSelect.addEventListener("change", () => {
        updateSelectClassColor(p1BotSelect);
        applyBotMatchup();
    });

    // 当前即时控制角色 (0 = 1P, 1 = 2P)
    let currentInstantActor = 0;
    const btnSelect1P = document.getElementById("btnSelect1P");
    const btnSelect2P = document.getElementById("btnSelect2P");
    const instantActorHint = document.getElementById("instantActorHint");

    if (btnSelect1P && btnSelect2P) {
        btnSelect1P.addEventListener("click", () => {
            currentInstantActor = 0;
            btnSelect1P.classList.add("active");
            btnSelect2P.classList.remove("active");
            if (instantActorHint) instantActorHint.textContent = "🎮 当前控制: 1P 我方";
        });
        btnSelect2P.addEventListener("click", () => {
            currentInstantActor = 1;
            btnSelect2P.classList.add("active");
            btnSelect1P.classList.remove("active");
            if (instantActorHint) instantActorHint.textContent = "🎮 当前控制: 2P 敌方 (动作由敌方发动)";
        });
    }

    // 出招按钮群 (支持 1P / 2P 动态切换)
    document.querySelectorAll(".btn-action").forEach(btn => {
        btn.addEventListener("click", () => {
            const action = parseInt(btn.dataset.action);
            const isLast = parseInt(btn.dataset.last);
            const hitIdx = parseInt(btn.dataset.hit || "0");
            if (!isNaN(action)) {
                sendAttack(currentInstantActor, action, hitIdx, isLast);
            }
        });
    });

    // 切换格挡 (支持当前控制角色)
    btnToggleBlock.addEventListener("click", async () => {
        p0Blocking = !p0Blocking;
        btnToggleBlock.textContent = p0Blocking ? "🛡️ 正在格挡 (点击解除)" : "🛡️ 切换格挡";
        btnToggleBlock.style.background = p0Blocking ? "#5c2b99" : "#21262d";
        await fetch("/api/block", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ player: currentInstantActor, blocking: p0Blocking ? 1 : 0 })
        });
        fetchState();
    });

    // 闪避按钮绑定 (后闪与侧闪)
    if (btnDashBack) {
        btnDashBack.addEventListener("click", () => sendDodge(currentInstantActor, 0));
    }
    if (btnSidestep) {
        btnSidestep.addEventListener("click", () => sendDodge(currentInstantActor, 1));
    }

    // 一键 5 连击 (L-L-L-M-M)
    btnCombo5.addEventListener("click", async () => {
        const combo = [
            { act: 1, last: 0 },
            { act: 1, last: 0 },
            { act: 1, last: 0 },
            { act: 2, last: 0 },
            { act: 2, last: 1 },
        ];
        for (let i = 0; i < combo.length; i++) {
            await sendAttack(currentInstantActor, combo[i].act, i, combo[i].last);
            await new Promise(r => setTimeout(r, 180));
        }
    });

    // =========================================================================
    // 战斗脚本设计器 (Combat Script Timeline Sequencer)
    // =========================================================================
    const SCRIPT_ACTIONS = {
        "dash_back": { icon: "💨", name: "后闪拉开距离", desc: "双方/单方后闪增大间距" },
        "sidestep": { icon: "💨", name: "侧闪闪避", desc: "侧向滑步闪避" },
        "heavy_start": { icon: "💥", name: "破防重击起手 (激活穿透力场)", desc: "进入重击蓄力，激活1.2s全程远程穿透" },
        "heavy_attack": { icon: "💥", name: "破防重击", desc: "破防重击造成伤害" },
        "ranged_attack": { icon: "🎯", name: "远程射击", desc: "远程弹道射击" },
        "light_1": { icon: "🥊", name: "L1 轻击 1", desc: "轻攻击第一击" },
        "light_2": { icon: "🥊", name: "L2 轻击 2", desc: "轻攻击第二击" },
        "light_3": { icon: "🥊", name: "L3 轻击 3", desc: "轻攻击第三击" },
        "light_4": { icon: "🥊", name: "L4 终结击", desc: "轻攻击终结击" },
        "med_1": { icon: "⚔️", name: "M1 中击 1", desc: "中攻击第一击" },
        "med_2": { icon: "⚔️", name: "M2 终结击", desc: "中攻击终结击" },
        "sp1": { icon: "⚡", name: "特殊技 1 (SP1)", desc: "释放1格特技" },
        "sp2": { icon: "⚡⚡", name: "特殊技 2 (SP2)", desc: "释放2格特技" },
        "sp3": { icon: "⚡⚡⚡", name: "特殊技 3 (SP3)", desc: "释放3格终极技" },
        "block_on": { icon: "🛡️", name: "开启格挡", desc: "进入格挡防御" },
        "block_off": { icon: "🛡️", name: "解除格挡", desc: "解除防御姿态" },
        "inject_buff": { icon: "💉", name: "注入状态", desc: "施加Buff/Debuff" },
        "delay": { icon: "⏱️", name: "单纯等待", desc: "仅间隔延时" },
    };

    let scriptSteps = [];
    let isScriptRunning = false;
    let abortScriptPlayback = false;
    let dragSrcIndex = -1;

    // DOM Elements
    const tabScript = document.getElementById("tabScript");
    const tabInstant = document.getElementById("tabInstant");
    const tabPreset = document.getElementById("tabPreset");
    const panelScript = document.getElementById("panelScript");
    const panelInstant = document.getElementById("panelInstant");
    const panelPreset = document.getElementById("panelPreset");

    const btnPlayScript = document.getElementById("btnPlayScript");
    const btnStopScript = document.getElementById("btnStopScript");
    const scriptStatusBadge = document.getElementById("scriptStatusBadge");
    const scriptStepList = document.getElementById("scriptStepList");
    const stepCount = document.getElementById("stepCount");

    const stepActor = document.getElementById("stepActor");
    const stepAction = document.getElementById("stepAction");
    const buffSelectRow = document.getElementById("buffSelectRow");
    const stepBuffId = document.getElementById("stepBuffId");
    const stepDelay = document.getElementById("stepDelay");
    const btnAddStep = document.getElementById("btnAddStep");

    const btnPresetWbPenetrate = document.getElementById("btnPresetWbPenetrate");
    const btnPresetWbSp1 = document.getElementById("btnPresetWbSp1");
    const btnClearScript = document.getElementById("btnClearScript");

    // Workspace Tabs Switcher
    function setupWorkspaceTabs() {
        const tabs = [
            { btn: tabScript, panel: panelScript },
            { btn: tabInstant, panel: panelInstant },
            { btn: tabPreset, panel: panelPreset },
        ];
        tabs.forEach(t => {
            if (!t.btn || !t.panel) return;
            t.btn.addEventListener("click", () => {
                tabs.forEach(o => {
                    if (o.btn) o.btn.classList.remove("active");
                    if (o.panel) o.panel.classList.remove("active");
                });
                t.btn.classList.add("active");
                t.panel.classList.add("active");
            });
        });
    }
    setupWorkspaceTabs();

    // Toggle buff select row on action change
    if (stepAction && buffSelectRow) {
        stepAction.addEventListener("change", () => {
            buffSelectRow.style.display = (stepAction.value === "inject_buff") ? "flex" : "none";
        });
    }

    // Load from storage or default
    function initScript() {
        try {
            const saved = localStorage.getItem("tftf_sim_script");
            if (saved) {
                scriptSteps = JSON.parse(saved);
            }
        } catch(e) {}
        if (!scriptSteps || scriptSteps.length === 0) {
            loadPresetWindbladePenetrate();
        } else {
            renderScriptStepList();
        }
    }

    function saveScriptToStorage() {
        try {
            localStorage.setItem("tftf_sim_script", JSON.stringify(scriptSteps));
        } catch(e) {}
    }

    // Render Steps List with HTML5 Drag & Drop
    function renderScriptStepList() {
        if (!scriptStepList) return;
        scriptStepList.innerHTML = "";
        if (stepCount) stepCount.textContent = scriptSteps.length;

        if (scriptSteps.length === 0) {
            scriptStepList.innerHTML = `
                <div class="step-empty-hint">
                    <span>📭 脚本序列为空</span>
                    <span>点击右侧【➕ 插入到事件序列】或顶部【🌟 载入风刃重击穿透测试】开始编排</span>
                </div>
            `;
            return;
        }

        scriptSteps.forEach((step, idx) => {
            const card = document.createElement("div");
            card.className = "script-step-card";
            card.draggable = true;
            card.dataset.index = idx;

            // Actor tag
            let actorHtml = '<span class="step-actor-pill actor-both">双方</span>';
            if (step.actor === "0") actorHtml = '<span class="step-actor-pill actor-p0">1P 我方</span>';
            else if (step.actor === "1") actorHtml = '<span class="step-actor-pill actor-p1">2P 敌方</span>';

            const actInfo = SCRIPT_ACTIONS[step.action] || { icon: "⚡", name: step.action, desc: "" };
            let actName = `${actInfo.icon} ${actInfo.name}`;
            if (step.action === "inject_buff" && step.buffId) {
                actName = `💉 注入: ${step.buffId}`;
            }

            card.innerHTML = `
                <span class="step-handle" title="按住拖拽排序">⋮⋮</span>
                <span class="step-idx">#${idx + 1}</span>
                ${actorHtml}
                <div class="step-info" title="${actInfo.desc}">
                    <span class="step-name">${actName}</span>
                </div>
                <span class="step-delay-tag">⏱️ ${step.delayMs || 300}ms</span>
                <div class="step-actions">
                    <button class="btn-step-mini btn-step-up" title="上移" ${idx === 0 ? "disabled style='opacity:0.3'" : ""}>🔼</button>
                    <button class="btn-step-mini btn-step-down" title="下移" ${idx === scriptSteps.length - 1 ? "disabled style='opacity:0.3'" : ""}>🔽</button>
                    <button class="btn-step-mini btn-step-del" title="删除本步">❌</button>
                </div>
            `;

            // Drag and Drop events
            card.addEventListener("dragstart", (e) => {
                dragSrcIndex = idx;
                e.dataTransfer.effectAllowed = "move";
                card.classList.add("dragging");
            });

            card.addEventListener("dragend", () => {
                card.classList.remove("dragging");
                document.querySelectorAll(".script-step-card").forEach(c => c.classList.remove("drag-over"));
            });

            card.addEventListener("dragover", (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = "move";
                card.classList.add("drag-over");
            });

            card.addEventListener("dragleave", () => {
                card.classList.remove("drag-over");
            });

            card.addEventListener("drop", (e) => {
                e.preventDefault();
                card.classList.remove("drag-over");
                const destIndex = idx;
                if (dragSrcIndex >= 0 && dragSrcIndex !== destIndex) {
                    const item = scriptSteps.splice(dragSrcIndex, 1)[0];
                    scriptSteps.splice(destIndex, 0, item);
                    saveScriptToStorage();
                    renderScriptStepList();
                }
            });

            // Button actions
            card.querySelector(".btn-step-up").addEventListener("click", (e) => {
                e.stopPropagation();
                if (idx > 0) {
                    const temp = scriptSteps[idx];
                    scriptSteps[idx] = scriptSteps[idx - 1];
                    scriptSteps[idx - 1] = temp;
                    saveScriptToStorage();
                    renderScriptStepList();
                }
            });

            card.querySelector(".btn-step-down").addEventListener("click", (e) => {
                e.stopPropagation();
                if (idx < scriptSteps.length - 1) {
                    const temp = scriptSteps[idx];
                    scriptSteps[idx] = scriptSteps[idx + 1];
                    scriptSteps[idx + 1] = temp;
                    saveScriptToStorage();
                    renderScriptStepList();
                }
            });

            card.querySelector(".btn-step-del").addEventListener("click", (e) => {
                e.stopPropagation();
                scriptSteps.splice(idx, 1);
                saveScriptToStorage();
                renderScriptStepList();
            });

            scriptStepList.appendChild(card);
        });
    }

    // Add Step Form
    if (btnAddStep) {
        btnAddStep.addEventListener("click", () => {
            const actor = stepActor.value;
            const action = stepAction.value;
            const buffId = stepBuffId ? stepBuffId.value : "power_gain";
            const delayMs = parseInt(stepDelay.value) || 350;

            scriptSteps.push({
                id: "s_" + Date.now() + "_" + Math.floor(Math.random() * 1000),
                actor,
                action,
                buffId: (action === "inject_buff") ? buffId : undefined,
                delayMs
            });

            saveScriptToStorage();
            renderScriptStepList();
        });
    }

    // Presets
    function loadPresetSlipstreamPenetrate() {
        scriptSteps = [
            { id: "s1", actor: "both", action: "dash_back", delayMs: 350 },
            { id: "s2", actor: "1", action: "ranged_attack", delayMs: 150 },
            { id: "s3", actor: "0", action: "heavy_start", delayMs: 250 },
            { id: "s4", actor: "0", action: "heavy_attack", delayMs: 400 },
        ];
        saveScriptToStorage();
        renderScriptStepList();
        if (typeof showToast === "function") showToast("🌟 已载入：滑流重击远程穿透测试脚本 (穿透规避)");
    }

    function loadPresetWindbladePenetrate() {
        scriptSteps = [
            { id: "s1", actor: "both", action: "dash_back", delayMs: 350 },
            { id: "s2", actor: "1", action: "ranged_attack", delayMs: 150 },
            { id: "s3", actor: "0", action: "heavy_start", delayMs: 250 },
            { id: "s4", actor: "0", action: "heavy_attack", delayMs: 400 },
        ];
        saveScriptToStorage();
        renderScriptStepList();
        if (typeof showToast === "function") showToast("🌟 已载入：风刃重击穿透远程测试脚本");
    }

    function loadPresetWindbladeSp1() {
        scriptSteps = [
            { id: "s1", actor: "both", action: "dash_back", delayMs: 300 },
            { id: "s2", actor: "1", action: "inject_buff", buffId: "power_gain", delayMs: 300 },
            { id: "s3", actor: "0", action: "sp1", delayMs: 500 },
        ];
        saveScriptToStorage();
        renderScriptStepList();
        if (typeof showToast === "function") showToast("⚡ 已载入：风刃SP1驱散瞬伤与震击测试脚本");
    }

    if (btnPresetWbPenetrate) btnPresetWbPenetrate.addEventListener("click", loadPresetWindbladePenetrate);
    if (btnPresetWbSp1) btnPresetWbSp1.addEventListener("click", loadPresetWindbladeSp1);
    const btnPresetSsPenetrate = document.getElementById("btnPresetSsPenetrate");
    if (btnPresetSsPenetrate) btnPresetSsPenetrate.addEventListener("click", loadPresetSlipstreamPenetrate);
    if (btnClearScript) {
        btnClearScript.addEventListener("click", () => {
            if (confirm("确定清空当前脚本事件序列吗？")) {
                scriptSteps = [];
                saveScriptToStorage();
                renderScriptStepList();
            }
        });
    }

    // Playback Execution
    async function executeStep(step) {
        const actor = step.actor;
        const act = step.action;

        if (act === "dash_back") {
            if (actor === "both") {
                sendDodge(0, 0);
                sendDodge(1, 0);
            } else {
                sendDodge(parseInt(actor), 0);
            }
        } else if (act === "sidestep") {
            if (actor === "both") {
                sendDodge(0, 1);
                sendDodge(1, 1);
            } else {
                sendDodge(parseInt(actor), 1);
            }
        } else if (act === "heavy_start") {
            const atker = (actor === "both" || actor === "0") ? 0 : 1;
            await fetch("/api/attack_start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ attacker: atker, action: 4 })
            });
            const fighter = (atker === 0) ? fighterP0 : fighterP1;
            if (fighter) {
                fighter.classList.add("attack-react");
                setTimeout(() => fighter.classList.remove("attack-react"), 300);
            }
            fetchState();
        } else if (act === "heavy_attack") {
            const atker = (actor === "both" || actor === "0") ? 0 : 1;
            await sendAttack(atker, 4, 0, 1);
        } else if (act === "ranged_attack") {
            const atker = (actor === "both" || actor === "1") ? 1 : 0;
            await sendAttack(atker, 8, 0, 1);
        } else if (act === "light_1") {
            const atker = (actor === "1") ? 1 : 0;
            await sendAttack(atker, 1, 0, 0);
        } else if (act === "light_2") {
            const atker = (actor === "1") ? 1 : 0;
            await sendAttack(atker, 1, 1, 0);
        } else if (act === "light_3") {
            const atker = (actor === "1") ? 1 : 0;
            await sendAttack(atker, 1, 2, 0);
        } else if (act === "light_4") {
            const atker = (actor === "1") ? 1 : 0;
            await sendAttack(atker, 1, 3, 1);
        } else if (act === "med_1") {
            const atker = (actor === "1") ? 1 : 0;
            await sendAttack(atker, 2, 0, 0);
        } else if (act === "med_2") {
            const atker = (actor === "1") ? 1 : 0;
            await sendAttack(atker, 2, 1, 1);
        } else if (act === "sp1") {
            const atker = (actor === "1") ? 1 : 0;
            await sendAttack(atker, 16, 0, 1);
        } else if (act === "sp2") {
            const atker = (actor === "1") ? 1 : 0;
            await sendAttack(atker, 32, 0, 1);
        } else if (act === "sp3") {
            const atker = (actor === "1") ? 1 : 0;
            await sendAttack(atker, 64, 0, 1);
        } else if (act === "block_on") {
            const p = (actor === "1") ? 1 : 0;
            await fetch("/api/block", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ player: p, blocking: 1 })
            });
            fetchState();
        } else if (act === "block_off") {
            const p = (actor === "1") ? 1 : 0;
            await fetch("/api/block", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ player: p, blocking: 0 })
            });
            fetchState();
        } else if (act === "inject_buff") {
            const target = (actor === "0") ? 0 : 1;
            const bid = step.buffId || "power_gain";
            await fetch("/api/inject_buff", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ target: target, mod_id: bid, dur: 8.0, stacks: 1 })
            });
            fetchState();
        }
    }

    async function playScript() {
        if (isScriptRunning) return;
        if (scriptSteps.length === 0) {
            loadPresetWindbladePenetrate();
        }

        isScriptRunning = true;
        abortScriptPlayback = false;
        if (btnPlayScript) btnPlayScript.disabled = true;
        if (btnStopScript) btnStopScript.disabled = false;
        if (scriptStatusBadge) {
            scriptStatusBadge.textContent = "▶️ 正在执行...";
            scriptStatusBadge.className = "script-status-badge running";
        }

        const cards = scriptStepList ? scriptStepList.querySelectorAll(".script-step-card") : [];

        for (let i = 0; i < scriptSteps.length; i++) {
            if (abortScriptPlayback) break;
            const step = scriptSteps[i];
            if (scriptStatusBadge) {
                scriptStatusBadge.textContent = `▶️ 步骤 ${i + 1}/${scriptSteps.length}`;
            }

            cards.forEach((c, idx) => {
                c.classList.remove("step-running");
                if (idx === i) c.classList.add("step-running");
                if (idx < i) c.classList.add("step-done");
            });

            if (cards[i]) {
                cards[i].scrollIntoView({ behavior: "smooth", block: "nearest" });
            }

            await executeStep(step);
            await new Promise(r => setTimeout(r, step.delayMs || 350));
        }

        cards.forEach(c => c.classList.remove("step-running"));
        if (abortScriptPlayback) {
            if (scriptStatusBadge) {
                scriptStatusBadge.textContent = "⏹ 已停止";
                scriptStatusBadge.className = "script-status-badge stopped";
            }
        } else {
            if (scriptStatusBadge) {
                scriptStatusBadge.textContent = "✅ 播放完成";
                scriptStatusBadge.className = "script-status-badge done";
            }
            cards.forEach(c => c.classList.add("step-done"));
        }

        isScriptRunning = false;
        if (btnPlayScript) btnPlayScript.disabled = false;
        if (btnStopScript) btnStopScript.disabled = true;
    }

    if (btnPlayScript) btnPlayScript.addEventListener("click", playScript);
    if (btnStopScript) {
        btnStopScript.addEventListener("click", () => {
            abortScriptPlayback = true;
        });
    }

    initScript();

    // 预设剧本按钮
    document.getElementById("presetOptimus").addEventListener("click", setupPresetOptimus);
    document.getElementById("presetMegatron").addEventListener("click", setupPresetMegatron);
    document.getElementById("presetProwl").addEventListener("click", setupPresetProwl);
    const presetBumblebee = document.getElementById("presetBumblebee");
    if (presetBumblebee) {
        presetBumblebee.addEventListener("click", setupPresetBumblebee);
    }
    const presetWindbladeSp1 = document.getElementById("presetWindbladeSp1");
    if (presetWindbladeSp1) {
        presetWindbladeSp1.addEventListener("click", setupPresetWindbladeSp1);
    }
    const presetWindbladeStun = document.getElementById("presetWindbladeStun");
    if (presetWindbladeStun) {
        presetWindbladeStun.addEventListener("click", setupPresetWindbladeStun);
    }

    const presetSlipstreamPurify = document.getElementById("presetSlipstreamPurify");
    if (presetSlipstreamPurify) {
        presetSlipstreamPurify.addEventListener("click", setupPresetSlipstreamPurify);
    }

    const presetSlipstreamExploit = document.getElementById("presetSlipstreamExploit");
    if (presetSlipstreamExploit) {
        presetSlipstreamExploit.addEventListener("click", setupPresetSlipstreamExploit);
    }

    const presetNecroOverwhelming = document.getElementById("presetNecroOverwhelming");
    if (presetNecroOverwhelming) {
        presetNecroOverwhelming.addEventListener("click", setupPresetNecroOverwhelming);
    }

    const presetNecroPowerDebuff = document.getElementById("presetNecroPowerDebuff");
    if (presetNecroPowerDebuff) {
        presetNecroPowerDebuff.addEventListener("click", setupPresetNecroPowerDebuff);
    }

    // 日志清空
    btnClearLogs.addEventListener("click", () => {
        logTerminal.innerHTML = "";
    });

    // 注入 Buff 模态框
    document.getElementById("btnInjectP0").addEventListener("click", () => openInjectModal(0));
    document.getElementById("btnInjectP1").addEventListener("click", () => openInjectModal(1));
    btnModalClose.addEventListener("click", closeInjectModal);
    btnModalCancel.addEventListener("click", closeInjectModal);

    modalBuffSelect.addEventListener("change", () => {
        customBuffGroup.style.display = (modalBuffSelect.value === "custom") ? "flex" : "none";
    });

    btnModalApply.addEventListener("click", async () => {
        let modId = modalBuffSelect.value;
        if (modId === "custom") {
            modId = modalCustomBuffId.value.trim();
        }
        const dur = parseFloat(modalBuffDur.value) || 6.0;
        const stacks = parseInt(modalBuffStacks.value) || 1;

        if (modId) {
            await fetch("/api/inject_buff", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ target: currentInjectTarget, mod_id: modId, dur, stacks })
            });
            fetchState();
            closeInjectModal();
            showToast(`已向 ${currentInjectTarget === 0 ? "1P" : "2P"} 注入 ${modId} x${stacks}`);
        }
    });
}

// ---------------------------------------------------------------------------
// 预设场景一键测试 (Presets)
// ---------------------------------------------------------------------------
async function setupPresetOptimus() {
    p0BotSelect.value = "optimusprime_cin_tf";
    p1BotSelect.value = "bonecrusher_cin_rotf";
    await applyBotMatchup();
    // 注入两层流血
    await fetch("/api/inject_buff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: 0, mod_id: "dmg_bleed", dur: 6.0, stacks: 2 })
    });
    showToast("📌 场景已装载: 斗擎挂 2 层流血！点【▶ 开始模拟】观察 1s 后净化");
    fetchState();
}

async function setupPresetMegatron() {
    p0BotSelect.value = "megatron_gs_leader2015";
    p1BotSelect.value = "sharkticon_gs_demolition";
    await applyBotMatchup();
    // 威震天充能 3 层
    await fetch("/api/inject_buff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: 0, mod_id: "megatron_fusion_cannon", dur: -1.0, stacks: 3 })
    });
    // 鲨鱼精挂感电与破甲
    await fetch("/api/inject_buff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: 1, mod_id: "megatron_sp3_shock", dur: 8.0, stacks: 1 })
    });
    await fetch("/api/inject_buff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: 1, mod_id: "megatron_sp1_armor_break", dur: 8.0, stacks: 1 })
    });
    showToast("📌 场景已装载: 威震天满充能 vs 鲨鱼精带减益！点击【💥 破防重击】验证融合");
    fetchState();
}

async function setupPresetProwl() {
    p0BotSelect.value = "prowl_gs_deluxe2016";
    p1BotSelect.value = "bonecrusher_cin_rotf";
    await applyBotMatchup();
    showToast("📌 场景已装载: 警车！点击【💨 后闪】开始充能蓄力，出手时转换为近战增益");
    fetchState();
}

async function setupPresetBumblebee() {
    p0BotSelect.value = "bumblebee_gs_kabam";
    p1BotSelect.value = "bonecrusher_cin_rotf";
    await applyBotMatchup();
    showToast("📌 场景已装载: 小黄蜂！点击【💨 后闪】获得规避，点击【💨 侧闪】叠加暴击增益");
    fetchState();
}

async function setupPresetWindbladeSp1() {
    p0BotSelect.value = "windblade_gs";
    p1BotSelect.value = "bonecrusher_cin_rotf";
    await applyBotMatchup();
    // 给敌方注入 2 层能量获取增益
    await fetch("/api/inject_buff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: 1, mod_id: "power_gain", dur: 10.0, stacks: 2 })
    });
    // 增加风刃自身能量至 1.0，直接具备 SP1 释放条件
    await fetch("/api/mana", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player: 0, mana: 1.0 })
    });
    showToast("📌 场景已装载: 敌方注入 2 层能量获取增益！风刃能量已就绪，点击【⚡ SP1 (1格)】测试驱散与80%瞬伤！");
    fetchState();
}

async function setupPresetWindbladeStun() {
    p0BotSelect.value = "windblade_gs";
    p1BotSelect.value = "bonecrusher_cin_rotf";
    await applyBotMatchup();
    // 给敌方注入流血
    await fetch("/api/inject_buff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: 1, mod_id: "dmg_bleed", dur: 8.0, stacks: 1 })
    });
    showToast("📌 场景已装载: 敌方处于流血状态！点击【🎯 远程射击】测试 35% 远程流血压制眩晕");
    fetchState();
}

async function setupPresetSlipstreamPurify() {
    p0BotSelect.value = "slipstream_gs";
    p1BotSelect.value = "bonecrusher_cin_rotf";
    await applyBotMatchup();
    // 给自身注入震击
    await fetch("/api/inject_buff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: 0, mod_id: "dmg_shock", dur: 10.0, stacks: 1 })
    });
    showToast("📌 场景已装载: 滑流处于震击状态！单按【M2 终结击】测试净化自身震击并反噬对手 8s 震击与 10% 暴率！");
    fetchState();
}

async function setupPresetSlipstreamExploit() {
    p0BotSelect.value = "slipstream_gs";
    p1BotSelect.value = "bonecrusher_cin_rotf";
    await applyBotMatchup();
    // 给敌方注入 3 种减益
    await fetch("/api/inject_buff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: 1, mod_id: "slipstream_crit_resist_down", dur: 4.0, stacks: 1 })
    });
    await fetch("/api/inject_buff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: 1, mod_id: "slipstream_power_drain", dur: 4.0, stacks: 1 })
    });
    await fetch("/api/inject_buff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: 1, mod_id: "slipstream_backfire", dur: 4.0, stacks: 1 })
    });
    showToast("📌 场景已装载: 敌方注入 3 种减益！轻击/远程命中测试【利用弱点】随机刷新其中 1 个减益持续时间！");
    fetchState();
}

async function setupPresetNecroOverwhelming() {
    p0BotSelect.value = "necrotronus_gs_kabam";
    p1BotSelect.value = "bonecrusher_cin_rotf";
    await applyBotMatchup();
    // 注入 20 层泰坦充能
    await fetch("/api/inject_buff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: 0, mod_id: "necrotronus_titan_charge", dur: -1.0, stacks: 20 })
    });
    await fetch("/api/attack", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ attacker: 0, action: 1, hit_idx: 0, is_last: 0, blocked: 0 })
    });
    showToast("📌 场景已装载: 亡灵天尊达到 20 层泰坦充能，进入势不可挡模式！任意攻击 100% 施加 6 秒流血！");
    fetchState();
}

async function setupPresetNecroPowerDebuff() {
    p0BotSelect.value = "necrotronus_gs_kabam";
    p1BotSelect.value = "bonecrusher_cin_rotf";
    await applyBotMatchup();
    // 我方 0.5 格气，敌方 1.5 格气
    await fetch("/api/mana", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player: 0, mana: 0.5 })
    });
    await fetch("/api/mana", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player: 1, mana: 1.5 })
    });
    await fetch("/api/tick", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dt_ms: 100 })
    });
    showToast("📌 场景已装载: 敌方能量高于亡灵天尊，触发红色 E606 能量压制减益(-30%功率)！");
    fetchState();
}

async function applyBotMatchup() {
    const p0 = p0BotSelect.value;
    const p1 = p1BotSelect.value;
    const p0Text = p0BotSelect.options[p0BotSelect.selectedIndex]?.text.split(" (")[0] || p0;
    const p1Text = p1BotSelect.options[p1BotSelect.selectedIndex]?.text.split(" (")[0] || p1;

    if (p0Name) p0Name.textContent = p0Text;
    if (p1Name) p1Name.textContent = p1Text;
    if (stageP0Name) stageP0Name.textContent = p0Text;
    if (stageP1Name) stageP1Name.textContent = p1Text;

    const b0 = g_allBots.find(b => b.bot_id === p0);
    const b1 = g_allBots.find(b => b.bot_id === p1);
    const p0IdEl = document.getElementById("p0BotId");
    const p1IdEl = document.getElementById("p1BotId");
    if (p0IdEl && b0) p0IdEl.textContent = `${b0.name_en} · ${b0.bot_id}`;
    if (p1IdEl && b1) p1IdEl.textContent = `${b1.name_en} · ${b1.bot_id}`;

    updateSelectClassColor(p0BotSelect);
    updateSelectClassColor(p1BotSelect);

    await fetch("/api/init", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ p0_bot_id: p0, p1_bot_id: p1, p0_hp: 15000, p1_hp: 15000, p0_atk: 1000, p1_atk: 1000 })
    });
    fetchState();
}

async function sendAttack(attacker, action, hit_idx, is_last) {
    const atkerFighter = (attacker === 0) ? fighterP0 : fighterP1;
    if (atkerFighter) {
        atkerFighter.classList.remove("attack-react");
        void atkerFighter.offsetWidth;
        atkerFighter.classList.add("attack-react");
        setTimeout(() => atkerFighter.classList.remove("attack-react"), 250);
    }

    await fetch("/api/attack", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ attacker, action, hit_idx, is_last, blocked: 0 })
    });
    fetchState();
}

async function sendDodge(player, type) {
    const fighter = (player === 0) ? fighterP0 : fighterP1;
    if (fighter) {
        fighter.classList.remove("dodge-react");
        void fighter.offsetWidth;
        fighter.classList.add("dodge-react");
        setTimeout(() => fighter.classList.remove("dodge-react"), 350);
    }

    await fetch("/api/dodge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player, type })
    });
    fetchState();
}

window.removeBuff = async function(target, mod_id) {
    await fetch("/api/remove_buff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target, mod_id, count: 1 })
    });
    fetchState();
};

function openInjectModal(target) {
    currentInjectTarget = target;
    modalTitle.textContent = `💉 手动注入状态 -> ${target === 0 ? "1P 我方" : "2P 敌方"}`;
    injectModal.style.display = "flex";
}

function closeInjectModal() {
    injectModal.style.display = "none";
}

function showToast(msg) {
    const toast = document.getElementById("toast");
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2200);
}

// 启动应用
document.addEventListener("DOMContentLoaded", init);


// ---------------------------------------------------------------------------
// 角色技能详情弹窗 (Ability Inspector Modal)
// ---------------------------------------------------------------------------
async function openAbilityModal(botId) {
    const modal = document.getElementById("abilityModal");
    const titleEl = document.getElementById("abModalBotName");
    const botIdEl = document.getElementById("abModalBotId");
    const avatarEl = document.getElementById("abModalAvatar");
    const implCountEl = document.getElementById("abImplementedCount");
    const allCountEl = document.getElementById("abAllCount");
    const implListEl = document.getElementById("abImplementedList");
    const allListEl = document.getElementById("abAllList");

    if (!modal) return;
    modal.style.display = "flex";
    botIdEl.textContent = botId;
    titleEl.textContent = "正在读取技能数据...";
    implListEl.innerHTML = '<div style="padding:24px;text-align:center;color:#64748b;">⏳ 正在读取代码实装能力与技能图鉴...</div>';
    allListEl.innerHTML = '';

    try {
        const res = await fetch(`/api/bot/${botId}`);
        const data = await res.json();
        const bot = data.bot || {};
        titleEl.textContent = `${bot.name_zh || botId} (能力总览)`;
        if (avatarEl) {
            avatarEl.textContent = (bot.faction === "decepticon") ? "😈" : "🤖";
        }

        const implemented = data.implemented_skills || [];
        const dbAbilities = data.db_abilities || [];
        implCountEl.textContent = implemented.length;
        allCountEl.textContent = dbAbilities.length;

        // 渲染代码已实装技能列表
        if (implemented.length === 0) {
            implListEl.innerHTML = '<div style="padding:24px;text-align:center;color:#64748b;">该角色暂无自定义 C/Python 机制，已载入标准引擎战斗属性。</div>';
        } else {
            implListEl.innerHTML = "";
            implemented.forEach(s => {
                let puaCode = 0xE406;
                if (s.pua_icon) {
                    puaCode = parseInt(s.pua_icon, s.pua_icon.startsWith("0x") ? 16 : 10);
                }
                const puaChar = String.fromCharCode(puaCode);
                const card = document.createElement("div");
                card.className = "ab-skill-card";
                card.innerHTML = `
                    <div class="ab-skill-glyph-wrap">
                        <span class="tecnica-icon ab-skill-glyph">${puaChar}</span>
                    </div>
                    <div class="ab-skill-info">
                        <div class="ab-skill-header">
                            <span class="ab-skill-title">${s.title}</span>
                            <span class="ab-skill-badge badge-active-c">${s.status || "C 引擎已实装"}</span>
                        </div>
                        <div class="ab-skill-category">[${s.category || "能力"}] · 矢量字符: U+${puaCode.toString(16).toUpperCase()}</div>
                        <div class="ab-skill-desc">${s.desc}</div>
                    </div>
                `;
                implListEl.appendChild(card);
            });
        }

        // 渲染官方全量技能列表
        if (dbAbilities.length === 0) {
            allListEl.innerHTML = '<div style="padding:24px;text-align:center;color:#64748b;">数据库中未检索到该角色技能记录。</div>';
        } else {
            allListEl.innerHTML = "";
            dbAbilities.forEach(a => {
                let puaCode = 0xE406;
                if (a.pua_icon) {
                    puaCode = parseInt(a.pua_icon, a.pua_icon.startsWith("0x") ? 16 : 10);
                }
                const puaChar = String.fromCharCode(puaCode);
                const card = document.createElement("div");
                card.className = "ab-skill-card";
                card.innerHTML = `
                    <div class="ab-skill-glyph-wrap" style="border-color:#64748b;">
                        <span class="tecnica-icon ab-skill-glyph" style="color:#94a3b8;">${puaChar}</span>
                    </div>
                    <div class="ab-skill-info">
                        <div class="ab-skill-header">
                            <span class="ab-skill-title">${a.title_zh || a.title_en || "未命名技能"}</span>
                            <span class="ab-skill-badge badge-active-db">官方图鉴</span>
                        </div>
                        <div class="ab-skill-category">[${a.category || "技能"}] ${a.title_en ? `· ${a.title_en}` : ""}</div>
                        <div class="ab-skill-desc">${a.desc_zh || a.desc_en || "暂无描述"}</div>
                    </div>
                `;
                allListEl.appendChild(card);
            });
        }
    } catch (e) {
        implListEl.innerHTML = `<div style="color:#ef4444;padding:20px;">加载技能失败: ${e.message}</div>`;
    }
}

function closeAbilityModal() {
    const modal = document.getElementById("abilityModal");
    if (modal) modal.style.display = "none";
}


// ---------------------------------------------------------------------------
// 环形圈 Buff DOM 差量更新 (复用节点，仅更新倒计时与层数，避免重复触发动画闪烁)
// ---------------------------------------------------------------------------
function renderBuffRingsDOM(container, buffs, playerIdx) {
    if (!container) return;
    if (!buffs || buffs.length === 0) {
        container.innerHTML = "";
        return;
    }

    const activeIds = new Set(buffs.map(b => b.id));

    // 1. 移除已过期的 DOM 节点
    Array.from(container.children).forEach(child => {
        const id = child.getAttribute("data-buff-id");
        if (!activeIds.has(id)) {
            child.remove();
        }
    });

    // 2. 对每个活跃 Buff 复用或新建 DOM
    buffs.forEach(b => {
        const info = getBuffPuaInfo(b.id);
        const isPerm = (b.rem_ms < 0);
        const isValid = (b.is_contract_valid !== false);
        const durMs = (b.dur_s && b.dur_s > 0) ? b.dur_s * 1000 : 7000;
        let pct = 1.0;
        if (!isPerm && durMs > 0) {
            pct = Math.max(0, Math.min(1.0, b.rem_ms / durMs));
        }
        const offset = (100 - pct * 100).toFixed(1);
        const timeText = isPerm ? "永久" : `${(b.rem_ms / 1000).toFixed(1)}s`;

        const puaChar = b.pua_char || info.char;
        const displayName = b.name || info.name || b.id;
        const tc = b.tc || (info.typeClass.includes("debuff") ? "ef4444" : "38bdf8");
        const gb = b.gb || tc;

        let item = null;
        for (let i = 0; i < container.children.length; i++) {
            if (container.children[i].getAttribute("data-buff-id") === b.id) {
                item = container.children[i];
                break;
            }
        }

        if (!item) {
            // 新创建节点：只在第一次添加时触发 ringPopIn 进场动画
            item = document.createElement("div");
            item.className = `buff-ring-item ${isPerm ? "is-perm" : ""} ${info.typeClass} ${!isValid ? "contract-violation" : ""}`;
            item.setAttribute("data-buff-id", b.id);
            item.onclick = () => removeBuff(playerIdx, b.id);

            item.innerHTML = `
                <div class="ring-svg-wrap">
                    <svg class="ring-svg" viewBox="0 0 40 40">
                        <circle class="ring-bg" cx="20" cy="20" r="16" />
                        <circle class="ring-progress" cx="20" cy="20" r="16" pathLength="100" />
                    </svg>
                    <div class="ring-icon-inner">
                        <span class="tecnica-icon">${puaChar}</span>
                    </div>
                    <span class="ring-stack-badge" style="display: none;"></span>
                    ${!isValid ? `<span class="ring-contract-warn" title="${b.contract_warning || '未在官方库注册'}">⚠️</span>` : ""}
                </div>
            `;
            container.appendChild(item);
        }

        // 差量更新数据
        item.title = `${displayName}\nID: ${b.id}\n剩余时间: ${timeText}\n层数: ${b.stacks}\nPUA: ${b.pua || info.hex}\n契约状态: ${isValid ? "✓ 官方能力库验证通过" : "⚠️ 契约违规 (未在Server/abilities定义)"}\n(点击驱散此状态)`;

        const progressCircle = item.querySelector(".ring-progress");
        if (progressCircle) {
            progressCircle.style.strokeDasharray = "100";
            progressCircle.style.strokeDashoffset = offset;
            if (tc) {
                progressCircle.style.stroke = "#" + tc;
                progressCircle.style.filter = `drop-shadow(0 0 5px #${gb})`;
            }
        }

        const iconEl = item.querySelector(".ring-icon-inner .tecnica-icon");
        if (iconEl) {
            iconEl.textContent = puaChar;
            if (tc) iconEl.style.color = "#" + tc;
        }

        const badge = item.querySelector(".ring-stack-badge");
        if (badge) {
            if (b.stacks > 1) {
                badge.textContent = b.stacks;
                badge.style.display = "block";
            } else {
                badge.style.display = "none";
            }
        }
    });
}
