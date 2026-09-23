import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Automatically append toolchain adb path if available
_toolchain_adb = Path(__file__).resolve().parent / "toolchain" / "android-sdk" / "platform-tools"
if _toolchain_adb.is_dir() and str(_toolchain_adb) not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{_toolchain_adb}{os.pathsep}{os.environ.get('PATH', '')}"

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText


HISTORY_FILE = Path.home() / ".tftf_adb_history.json"


# ---------------------------------------------------------------------------
# 1. 历史连接记录管理
# ---------------------------------------------------------------------------
def load_history() -> dict:
    """读取历史无线连接记录"""
    try:
        if HISTORY_FILE.exists():
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"recent_ips": [], "last_ip": "192.168.1.", "last_port": "5555", "use_fast_install": True}


def save_history(data: dict):
    """保存历史无线连接记录"""
    try:
        HISTORY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def record_history_ip_port(ip: str, port: str):
    """记录成功使用的 IP 与端口"""
    ip = ip.strip()
    port = port.strip() or "5555"
    if not ip:
        return
    hist = load_history()
    recent = hist.get("recent_ips", [])
    entry = f"{ip}:{port}"
    if entry in recent:
        recent.remove(entry)
    recent.insert(0, entry)
    hist["recent_ips"] = recent[:10]
    hist["last_ip"] = ip
    hist["last_port"] = port
    save_history(hist)


# ---------------------------------------------------------------------------
# 2. 设备识别与网络探测
# ---------------------------------------------------------------------------
def parse_adb_devices() -> list[dict]:
    """解析 adb devices -l 输出，区分有线与无线设备"""
    try:
        res = subprocess.run(
            ["adb", "devices", "-l"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return []

    lines = res.stdout.strip().splitlines()
    devices = []
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            serial = parts[0]
            status = parts[1]
            props = {}
            for item in parts[2:]:
                if ":" in item:
                    k, v = item.split(":", 1)
                    props[k] = v

            model = props.get("model", "")
            is_wireless = bool(re.search(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$", serial))

            conn_type = "无线" if is_wireless else "有线"
            icon = "📶" if is_wireless else "🔌"
            status_desc = {
                "device": "在线",
                "unauthorized": "未授权(手机点击允许)",
                "offline": "脱机",
            }.get(status, status)

            label = f"{icon} [{conn_type}] {serial}"
            if model:
                label += f" ({model} - {status_desc})"
            else:
                label += f" ({status_desc})"

            devices.append({
                "serial": serial,
                "status": status,
                "is_wireless": is_wireless,
                "model": model,
                "label": label,
            })
    return devices


def get_device_wifi_ip(serial: str) -> str:
    """尝试通过 shell 查询已连接有线设备的 Wi-Fi 局域网 IP"""
    for cmd in [
        ["adb", "-s", serial, "shell", "ip", "-f", "inet", "addr", "show", "wlan0"],
        ["adb", "-s", serial, "shell", "getprop", "dhcp.wlan0.ipaddress"],
        ["adb", "-s", serial, "shell", "ip", "route"],
    ]:
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
            m = re.search(r"inet\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", res.stdout)
            if m:
                return m.group(1)
            ip_str = res.stdout.strip()
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip_str):
                return ip_str
            m2 = re.search(r"wlan0.*src\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", res.stdout)
            if m2:
                return m2.group(1)
        except Exception:
            pass
    return ""


def get_local_ip(target_ip: str) -> str:
    """通过探测目标 IP 自动获取电脑当前通信所使用的局域网物理 IP"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((target_ip, 80))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def detect_downloader(device_id: str) -> str | None:
    """探测手机设备端可用的下载工具 (优先 /data/local/tmp/curl，其次系统 curl、wget、toybox wget)"""
    # 1. 优先 /data/local/tmp/curl
    try:
        res = subprocess.run(
            ["adb", "-s", device_id, "shell", "/data/local/tmp/curl", "--version"],
            capture_output=True, text=True, timeout=4
        )
        if res.returncode == 0:
            return "/data/local/tmp/curl"
    except Exception:
        pass

    # 2. 系统内置 curl
    try:
        res = subprocess.run(
            ["adb", "-s", device_id, "shell", "curl", "--version"],
            capture_output=True, text=True, timeout=4
        )
        if res.returncode == 0:
            return "curl"
    except Exception:
        pass

    # 3. 系统 wget
    try:
        res = subprocess.run(
            ["adb", "-s", device_id, "shell", "which", "wget"],
            capture_output=True, text=True, timeout=4
        )
        if res.returncode == 0 and "wget" in res.stdout:
            return "wget"
    except Exception:
        pass

    # 4. toybox wget
    try:
        res = subprocess.run(
            ["adb", "-s", device_id, "shell", "toybox", "wget", "--help"],
            capture_output=True, text=True, timeout=4
        )
        if res.returncode == 0:
            return "toybox wget"
    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# 3. 高性能 HTTP 局域网文件服务 (来自 INSTALL-OVER-LAN-FASTER.py)
# ---------------------------------------------------------------------------
class FastHTTPRequestHandler(SimpleHTTPRequestHandler):
    """为局域网大文件传输定制的高速 HTTP 处理器 (4MB 发送缓冲 + 2MB 读写块 + TCP_NODELAY)"""

    def copyfileobj(self, fsrc, fdst, length=2 * 1024 * 1024):
        shutil.copyfileobj(fsrc, fdst, length)

    def handle(self):
        try:
            self.request.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4 * 1024 * 1024)
            self.request.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except Exception:
            pass
        super().handle()

    def log_message(self, format, *args):
        pass


def start_http_server(serve_dir: str | Path) -> tuple[ThreadingHTTPServer, int]:
    handler = partial(FastHTTPRequestHandler, directory=str(serve_dir))
    httpd = ThreadingHTTPServer(("0.0.0.0", 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, port


def stop_http_server(httpd: ThreadingHTTPServer | None):
    if httpd:
        try:
            httpd.shutdown()
            httpd.server_close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 4. 设备截图功能
# ---------------------------------------------------------------------------
def capture_device_screenshot(device_id: str, output_file: Path) -> tuple[bool, str]:
    output_file = Path(output_file).resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        cmd = ["adb", "-s", device_id, "exec-out", "screencap", "-p"]
        res = subprocess.run(cmd, capture_output=True, timeout=12)
        if res.returncode == 0 and res.stdout.startswith(b"\x89PNG\r\n\x1a\n"):
            output_file.write_bytes(res.stdout)
            return True, f"截图已保存至: {output_file}"
    except Exception:
        pass

    try:
        remote_tmp = "/data/local/tmp/tftf_screencap.png"
        subprocess.run(["adb", "-s", device_id, "shell", "screencap", "-p", remote_tmp], check=True, timeout=12)
        subprocess.run(["adb", "-s", device_id, "pull", remote_tmp, str(output_file)], check=True, timeout=12)
        subprocess.run(["adb", "-s", device_id, "shell", "rm", "-f", remote_tmp], timeout=5)
        if output_file.exists() and output_file.stat().st_size > 0:
            return True, f"截图已保存至: {output_file}"
        return False, "未能从设备拉取到有效截图文件"
    except Exception as e:
        return False, f"ADB 截图执行失败: {e}"


# ---------------------------------------------------------------------------
# 5. 小米 / Android 10 及旧机型无线调试连接向导窗口
# ---------------------------------------------------------------------------
class WirelessGuideDialog(tk.Toplevel):
    """指导用户如何为没有原生无线调试开关的手机（如小米 8 / Android 10）快速建立无线调试"""

    def __init__(self, parent, on_trigger_usb_to_wifi=None):
        super().__init__(parent)
        self.title("📱 小米 / Android 10 旧机型无线调试指引")
        self.geometry("620x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_trigger_usb_to_wifi = on_trigger_usb_to_wifi

        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="📱 小米 8 / Android 10 及旧机型无线调试指南",
            font=("TkDefaultFont", 12, "bold"),
            foreground="#1a56db",
        ).pack(anchor="w", pady=(0, 8))

        guide_text = (
            "【为什么小米 8 / 旧系统没有无线调试开关？】\n"
            "• 设置中带“配对码”的原生无线调试开关是 Google 在 Android 11 才加入的功能。\n"
            "• 小米 8 官方最新系统停留于 MIUI 12.5 (底层 Android 10)，因此系统设置里没有该开关。\n"
            "• 但底层完全支持无线调试！只需插一次数据线激活一次端口，之后即可永久免插线无线调试！\n\n"
            "【极简 3 步操作步骤】：\n"
            "1. 开启手机调试开关：\n"
            "   打开「设置」->「更多设置」->「开发者选项」，开启「USB 调试」；\n"
            "   ⚠️ 小米必开：「USB 安装」与「USB 调试（安全设置）」(防止系统拦截安装)。\n\n"
            "2. 用 USB 数据线连上电脑：\n"
            "   手机上弹出授权提示框时，勾选“始终允许”并点击【确定】。\n\n"
            "3. 点击下方【⚡ 一键插线激活并转无线】按钮：\n"
            "   程序将全自动为您：读取手机 Wi-Fi IP -> 激活 5555 端口 -> 自动发起无线连接。\n"
            "   完成提示后，您就可以【拔掉 USB 数据线】了！\n\n"
            "💡 提示：日常只要不重启手机、保持在同一个 Wi-Fi，就可以一直无线连接使用；手机重启后只需再插一次线点一键激活即可。"
        )

        txt = ScrolledText(frame, wrap="word", height=16, font=("Consolas", 9), bg="#f8f9fa", fg="#212529")
        txt.insert(tk.END, guide_text)
        txt.config(state="disabled")
        txt.pack(fill="both", expand=True, pady=6)

        btn_box = ttk.Frame(frame)
        btn_box.pack(fill="x", pady=(10, 0))

        self.btn_action = ttk.Button(
            btn_box,
            text="⚡ 立即插线激活并转无线 (拔线随便用)",
            command=self._do_trigger,
        )
        self.btn_action.pack(side="left", padx=5)

        ttk.Button(btn_box, text="关闭", command=self.destroy).pack(side="right", padx=5)

    def _do_trigger(self):
        self.destroy()
        if self.on_trigger_usb_to_wifi:
            self.on_trigger_usb_to_wifi()


# ---------------------------------------------------------------------------
# 6. 图形化应用核心 (GUI)
# ---------------------------------------------------------------------------
class ApkInstallerApp:

    def __init__(self, root):
        self.root = root
        self.root.title("ADB APK 极速安装与有线/无线管理工具 (集成局域网直传引擎)")
        self.root.geometry("720x680")
        self.root.minsize(620, 540)

        # 变量绑定
        self.selected_device = tk.StringVar()
        self.device_map = {}  # label -> serial
        self.manual_ip = tk.StringVar()
        self.manual_port = tk.StringVar(value="5555")
        self.apk_path = tk.StringVar()
        self.use_fast_install = tk.BooleanVar(value=True)
        self.install_args = tk.StringVar(value="-r --no-incremental")
        self.screenshot_filename = tk.StringVar(value="")

        self._create_widgets()
        self._load_cached_history()
        self.refresh_devices()

    def _create_widgets(self):
        pad_opts = {"padx": 10, "pady": 4}

        # 1. 设备选择与连接区域
        dev_frame = ttk.LabelFrame(self.root, text="设备发现与连接", padding=8)
        dev_frame.pack(fill="x", **pad_opts)

        # 1.1 当前目标设备选择与转无线控制
        row_target = ttk.Frame(dev_frame)
        row_target.pack(fill="x", pady=(0, 6))

        ttk.Label(row_target, text="目标设备:").pack(side="left", padx=5)
        self.device_combo = ttk.Combobox(
            row_target,
            textvariable=self.selected_device,
            state="readonly",
            width=28,
        )
        self.device_combo.pack(side="left", fill="x", expand=True, padx=5)

        self.btn_refresh = ttk.Button(
            row_target, text="🔄 刷新", command=self.refresh_devices
        )
        self.btn_refresh.pack(side="left", padx=2)

        self.btn_usb_to_wifi = ttk.Button(
            row_target,
            text="⚡ 插线转无线 (拔线随便用)",
            command=self.start_usb_to_wireless_thread,
        )
        self.btn_usb_to_wifi.pack(side="left", padx=3)

        self.btn_guide = ttk.Button(
            row_target,
            text="❓ 小米无线指引",
            command=self.open_wireless_guide_dialog,
        )
        self.btn_guide.pack(side="left", padx=2)

        # 1.2 手动输入 IP 与 端口 连接无线设备
        row_manual = ttk.Frame(dev_frame)
        row_manual.pack(fill="x", pady=(2, 0))

        ttk.Label(row_manual, text="无线 IP:").pack(side="left", padx=(5, 2))
        self.combo_ip = ttk.Combobox(
            row_manual,
            textvariable=self.manual_ip,
            width=18,
        )
        self.combo_ip.pack(side="left", fill="x", expand=True, padx=2)
        self.combo_ip.bind("<<ComboboxSelected>>", self._on_history_ip_selected)

        ttk.Label(row_manual, text="端口:").pack(side="left", padx=(6, 2))
        self.entry_port = ttk.Entry(
            row_manual,
            textvariable=self.manual_port,
            width=8,
        )
        self.entry_port.pack(side="left", padx=2)

        self.btn_connect_manual = ttk.Button(
            row_manual, text="📶 连接无线", command=self.start_connect_manual_thread
        )
        self.btn_connect_manual.pack(side="left", padx=4)

        self.btn_disconnect_manual = ttk.Button(
            row_manual, text="❌ 断开无线", command=self.start_disconnect_manual_thread
        )
        self.btn_disconnect_manual.pack(side="left", padx=2)

        # 2. APK 选择区域
        file_frame = ttk.LabelFrame(self.root, text="APK 文件", padding=8)
        file_frame.pack(fill="x", **pad_opts)

        ttk.Entry(file_frame, textvariable=self.apk_path).pack(
            side="left", fill="x", expand=True, padx=5
        )
        ttk.Button(
            file_frame, text="📂 选择 APK", command=self.browse_apk
        ).pack(side="right", padx=5)

        # 3. 安装配置与传输模式区域
        param_frame = ttk.LabelFrame(self.root, text="安装参数与极速模式", padding=8)
        param_frame.pack(fill="x", **pad_opts)

        row_mode = ttk.Frame(param_frame)
        row_mode.pack(fill="x", pady=(0, 4))
        self.chk_fast = ttk.Checkbutton(
            row_mode,
            text="⚡ 启用局域网极速直传模式 (LAN HTTP 满速传输，强烈推荐无线调试，速度可达 30~80MB/s)",
            variable=self.use_fast_install,
            command=self._on_mode_toggled,
        )
        self.chk_fast.pack(side="left", padx=5)

        row_args = ttk.Frame(param_frame)
        row_args.pack(fill="x", pady=(2, 0))
        ttk.Label(row_args, text="额外参数:").pack(side="left", padx=5)
        ttk.Entry(row_args, textvariable=self.install_args).pack(
            side="left", fill="x", expand=True, padx=5
        )

        # 4. 操作按钮
        self.btn_install = ttk.Button(
            self.root, text="🚀 开始极速安装", command=self.start_install_thread
        )
        self.btn_install.pack(fill="x", padx=10, pady=6)

        # 5. 设备截图区域
        shot_frame = ttk.LabelFrame(self.root, text="设备截图", padding=8)
        shot_frame.pack(fill="x", **pad_opts)

        row_shot = ttk.Frame(shot_frame)
        row_shot.pack(fill="x", expand=True)

        ttk.Label(row_shot, text="自定义文件名:").pack(side="left", padx=5)
        self.entry_screenshot = ttk.Entry(
            row_shot, textvariable=self.screenshot_filename
        )
        self.entry_screenshot.pack(side="left", fill="x", expand=True, padx=5)

        self.btn_screenshot = ttk.Button(
            row_shot, text="📸 获取截图", command=self.start_screenshot_thread
        )
        self.btn_screenshot.pack(side="right", padx=5)

        self.btn_open_dir = ttk.Button(
            row_shot, text="📂 打开目录", command=self.open_screenshot_dir
        )
        self.btn_open_dir.pack(side="right", padx=5)

        ttk.Label(
            shot_frame,
            text="* 留空默认文件名: screenshot_YYYYMMDD_HHMMSS.png；若存在同名文件将默认直接覆盖",
            font=("TkDefaultFont", 8),
            foreground="gray",
        ).pack(anchor="w", padx=5, pady=(2, 0))

        # 6. 日志输出区域
        log_frame = ttk.LabelFrame(self.root, text="执行日志", padding=5)
        log_frame.pack(fill="both", expand=True, **pad_opts)

        self.log_text = ScrolledText(
            log_frame, wrap="word", height=8, bg="#1e1e1e", fg="#d4d4d4"
        )
        self.log_text.pack(fill="both", expand=True)

        # 7. 底部状态栏
        self.lbl_status = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.lbl_status.pack(fill="x", side=tk.BOTTOM, ipady=2)

    def log(self, message):
        """线程安全的日志输出"""
        def _append():
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
        self.root.after(0, _append)

    def set_status(self, text):
        """线程安全的状态栏更新"""
        self.root.after(0, lambda: self.lbl_status.config(text=text))

    def _on_mode_toggled(self):
        if self.use_fast_install.get():
            self.btn_install.config(text="🚀 开始极速安装 (LAN HTTP 局域网直传)")
        else:
            self.btn_install.config(text="🚀 开始标准安装 (ADB 流式传输)")

    def _load_cached_history(self):
        """载入历史 IP 列表"""
        hist = load_history()
        recent = hist.get("recent_ips", [])
        self.combo_ip["values"] = recent
        last_ip = hist.get("last_ip", "")
        last_port = hist.get("last_port", "5555")
        if last_ip:
            self.manual_ip.set(last_ip)
        else:
            self.manual_ip.set("192.168.1.")
        self.manual_port.set(last_port or "5555")
        self.use_fast_install.set(hist.get("use_fast_install", True))
        self._on_mode_toggled()

    def _on_history_ip_selected(self, event=None):
        val = self.manual_ip.get().strip()
        if ":" in val:
            ip, port = val.split(":", 1)
            self.manual_ip.set(ip)
            self.manual_port.set(port)

    def refresh_devices(self, notify_count: bool = True):
        devices = parse_adb_devices()
        self.device_map = {d["label"]: d["serial"] for d in devices}

        labels = [d["label"] for d in devices]
        self.device_combo["values"] = labels

        cur = self.selected_device.get()
        if labels:
            if cur not in labels:
                self.device_combo.current(0)
            if notify_count:
                usb_cnt = sum(1 for d in devices if not d["is_wireless"])
                wifi_cnt = sum(1 for d in devices if d["is_wireless"])
                self.log(f"[设备更新] 共发现 {len(devices)} 台设备（有线: {usb_cnt} 台，无线: {wifi_cnt} 台）")
        else:
            self.selected_device.set("")
            if notify_count:
                self.log("[提示] 未检测到任何已连接设备。可插上 USB 数据线，或输入手机无线 IP 点击【连接无线】。")

    def get_clean_device_id(self):
        label = self.selected_device.get().strip()
        if not label:
            return None
        if label in self.device_map:
            return self.device_map[label]
        for part in label.split():
            if not part.startswith("[") and not part.startswith("(") and part not in ["🔌", "📶"]:
                return part.strip("()")
        return None

    def open_wireless_guide_dialog(self):
        """弹出小米/旧机型无线调试指引窗口"""
        WirelessGuideDialog(self.root, on_trigger_usb_to_wifi=self.start_usb_to_wireless_thread)

    def start_usb_to_wireless_thread(self):
        """一键将当前有线连接的 USB 设备转为无线调试 (adb tcpip 5555 -> adb connect)"""
        dev_id = self.get_clean_device_id()
        if not dev_id:
            # 尝试刷新看看是否有刚插入的设备
            devices = parse_adb_devices()
            usb_devs = [d["serial"] for d in devices if not d["is_wireless"] and d["status"] == "device"]
            if usb_devs:
                dev_id = usb_devs[0]
            else:
                messagebox.showwarning(
                    "提示",
                    "未检测到已连接的 USB 设备！\n\n请先用 USB 数据线连上手机（如小米 8），并在手机屏幕弹窗点击【允许 USB 调试】后再试！\n若仍有问题请点击【❓ 小米无线指引】。"
                )
                return

        if ":" in dev_id:
            messagebox.showinfo("提示", f"设备 {dev_id} 当前已经是无线模式，无需转换，可直接拔线无线使用！")
            return

        self.btn_usb_to_wifi.config(state="disabled")
        self.set_status("正在激活手机无线调试端口...")
        self.log("=" * 50)
        self.log(f"🔌 正在尝试将 USB 设备 {dev_id} 切换为无线调试模式...")

        def _worker():
            try:
                # 1. 尝试自动查询手机 Wi-Fi 局域网 IP
                self.log("[*] 正在探测手机 Wi-Fi 局域网 IP...")
                ip = get_device_wifi_ip(dev_id)

                # 2. 执行 adb tcpip 5555 激活端口
                self.log("[*] 执行命令: adb tcpip 5555 (激活 TCP 监听模式)...")
                res_tcp = subprocess.run(
                    ["adb", "-s", dev_id, "tcpip", "5555"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                tcp_out = (res_tcp.stdout + res_tcp.stderr).strip()
                self.log(f"[ADB] {tcp_out}")

                if "restarting in TCP mode" not in tcp_out and "restarting" not in tcp_out and res_tcp.returncode != 0:
                    raise RuntimeError(f"激活端口失败: {tcp_out}")

                time.sleep(1.5)

                # 3. 如果没能自动检测到 IP，允许用户输入
                if not ip:
                    self.log("[!] 未能直接通过 Shell 读取到手机 Wi-Fi IP，正在请求用户确认...")
                    user_ip = tk.StringVar(value=self.manual_ip.get().strip() or "192.168.1.")

                    def _ask_ip():
                        dlg = tk.Toplevel(self.root)
                        dlg.title("输入手机 Wi-Fi IP")
                        dlg.geometry("420x180")
                        dlg.resizable(False, False)
                        dlg.transient(self.root)
                        dlg.grab_set()

                        ttk.Label(
                            dlg,
                            text="已成功激活 5555 端口！\n请查看手机「设置 -> WLAN -> 点击当前 Wi-Fi」中的 IP 地址：",
                            padding=10,
                        ).pack(anchor="w")

                        e = ttk.Entry(dlg, textvariable=user_ip, width=28)
                        e.pack(padx=20, pady=5)
                        e.focus()

                        def _ok():
                            dlg.destroy()

                        ttk.Button(dlg, text="确定连接", command=_ok).pack(pady=10)
                        self.root.wait_window(dlg)

                    self.root.after(0, _ask_ip)
                    # 等待弹窗关闭
                    while not user_ip.get() or user_ip.get().endswith("."):
                        time.sleep(0.5)
                        if not self.btn_usb_to_wifi.winfo_exists():
                            return
                    ip = user_ip.get().strip()

                target = f"{ip}:5555"
                self.log(f"[*] 正在自动连接无线目标: {target} ...")
                res_conn = subprocess.run(
                    ["adb", "connect", target],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                conn_out = (res_conn.stdout + res_conn.stderr).strip()
                self.log(f"[ADB] {conn_out}")

                if "connected to" in conn_out.lower():
                    record_history_ip_port(ip, "5555")
                    self.root.after(0, lambda: self.manual_ip.set(ip))
                    self.root.after(0, lambda: self.manual_port.set("5555"))
                    self.root.after(0, self._load_cached_history)
                    self.log(f"🎉 成功切换为无线调试模式 ({target})！您现在可以拔掉 USB 数据线了！")
                    self.root.after(0, lambda: messagebox.showinfo(
                        "切换成功 (可拔线)",
                        f"🎉 已成功开启并连接无线调试：\n{target}\n\n👉 您现在可以放心拔下 USB 数据线了！\n后续手机只要不重启、保持在同一 Wi-Fi，就可以一直无线使用！"
                    ))
                else:
                    self.log(f"⚠️ 无线连接返回: {conn_out}，请确认手机与电脑处于同一 Wi-Fi。")

            except Exception as e:
                self.log(f"[异常] 转换无线模式出错: {e}")
                self.root.after(0, lambda: messagebox.showerror("错误", f"切换无线调试失败: {e}"))
            finally:
                self.root.after(0, lambda: self.btn_usb_to_wifi.config(state="normal"))
                self.root.after(1000, lambda: self.refresh_devices(notify_count=False))
                self.set_status("就绪")

        threading.Thread(target=_worker, daemon=True).start()

    def start_connect_manual_thread(self):
        ip = self.manual_ip.get().strip()
        port = self.manual_port.get().strip()

        if ":" in ip:
            ip, port_in_ip = ip.split(":", 1)
            ip = ip.strip()
            port = port_in_ip.strip()
            self.manual_ip.set(ip)
            self.manual_port.set(port)

        if not ip:
            messagebox.showwarning("警告", "请输入手机无线 IP 地址！")
            return
        if not port:
            port = "5555"
            self.manual_port.set(port)

        target = f"{ip}:{port}"
        self.btn_connect_manual.config(state="disabled")
        self.log(f"📶 正在连接无线设备: {target} ...")

        def _worker():
            try:
                cmd = ["adb", "connect", target]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
                out = (res.stdout + res.stderr).strip()
                self.log(out)

                if "connected to" in out.lower():
                    record_history_ip_port(ip, port)
                    self.root.after(0, self._load_cached_history)
                    self.log(f"🎉 成功连接无线设备: {target}")
                else:
                    self.log(f"⚠️ 连接反馈: {out}")
            except Exception as e:
                self.log(f"[异常] 无线连接失败: {e}")
            finally:
                self.root.after(0, lambda: self.btn_connect_manual.config(state="normal"))
                self.root.after(600, lambda: self.refresh_devices(notify_count=False))

        threading.Thread(target=_worker, daemon=True).start()

    def start_disconnect_manual_thread(self):
        ip = self.manual_ip.get().strip()
        port = self.manual_port.get().strip() or "5555"
        if ":" in ip:
            target = ip
        elif ip and ip != "192.168.1.":
            target = f"{ip}:{port}"
        else:
            dev_id = self.get_clean_device_id()
            if dev_id and ":" in dev_id:
                target = dev_id
            else:
                messagebox.showwarning("警告", "请输入要断开的无线设备 IP 或选择已连接的无线设备！")
                return

        def _worker():
            try:
                cmd = ["adb", "disconnect", target]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
                out = (res.stdout + res.stderr).strip()
                self.log(f"🔌 {out}")
            except Exception as e:
                self.log(f"[异常] 断开失败: {e}")
            finally:
                self.root.after(600, lambda: self.refresh_devices(notify_count=False))

        threading.Thread(target=_worker, daemon=True).start()

    def browse_apk(self):
        file_selected = filedialog.askopenfilename(
            title="选择要安装的 APK",
            filetypes=[("APK 文件", "*.apk"), ("所有文件", "*.*")],
        )
        if file_selected:
            self.apk_path.set(file_selected)

    def start_install_thread(self):
        device_id = self.get_clean_device_id()
        apk = self.apk_path.get().strip()

        if not device_id:
            messagebox.showwarning("警告", "请先选择一个有效的已连接设备！")
            return

        if not apk or not os.path.exists(apk):
            messagebox.showwarning("警告", "请选择有效的 APK 文件路径！")
            return

        # 记住模式选择
        hist = load_history()
        hist["use_fast_install"] = self.use_fast_install.get()
        save_history(hist)

        self.btn_install.config(state="disabled")
        self.btn_refresh.config(state="disabled")

        if self.use_fast_install.get():
            target_fn = self._fast_install_worker
        else:
            target_fn = self._standard_install_worker

        thread = threading.Thread(target=target_fn, args=(device_id, apk), daemon=True)
        thread.start()

    # -----------------------------------------------------------------------
    # 极速局域网直传安装引擎 (来自 INSTALL-OVER-LAN-FASTER.py)
    # -----------------------------------------------------------------------
    def _fast_install_worker(self, device_id: str, apk: str):
        remote_tmp_apk = "/data/local/tmp/_fast_install_temp.apk"
        apk_path = Path(apk).resolve()
        apk_dir = apk_path.parent
        apk_name = apk_path.name
        httpd = None

        try:
            self.set_status("检查设备端下载组件...")
            self.log("=" * 50)
            self.log(f"⚡ [局域网极速直传模式] 准备安装: {apk_name}")
            self.log(f"目标设备: {device_id} ({'无线连接' if ':' in device_id else '有线连接'})")

            # 1. 探测手机可用下载工具
            downloader = detect_downloader(device_id)
            if not downloader:
                self.log("[!] 提示: 设备端未发现 curl 或 wget，将自动回退为标准 ADB 安装流...")
                return self._standard_install_worker(device_id, apk)

            self.log(f"[+] 选用设备端下载组件: {downloader}")

            # 2. 计算局域网 IP 并启动本地 HTTP 文件服务
            self.set_status("启动本地高速 HTTP 文件服务...")
            httpd, port = start_http_server(apk_dir)

            if ":" in device_id:
                phone_ip = device_id.split(":")[0]
            else:
                phone_ip = get_device_wifi_ip(device_id) or "192.168.1.1"

            local_ip = get_local_ip(phone_ip)
            encoded_name = urllib.parse.quote(apk_name)
            download_url = f"http://{local_ip}:{port}/{encoded_name}"
            self.log(f"[+] 本地直传节点已就绪: {download_url}")

            # 3. 手机端满速下载
            self.set_status("手机端正在满速下载 APK ...")
            self.log("[*] 正在通过千兆局域网满速向手机传输 APK 文件...")

            if "curl" in downloader:
                dl_cmd = f"{downloader} -fSL --connect-timeout 8 -o {remote_tmp_apk} '{download_url}'"
            else:
                dl_cmd = f"{downloader} -O {remote_tmp_apk} '{download_url}'"

            dl_res = subprocess.run(
                ["adb", "-s", device_id, "shell", dl_cmd],
                capture_output=True, text=True, timeout=180
            )

            # 传输完毕立即关闭本地 HTTP 服务
            stop_http_server(httpd)
            httpd = None

            if dl_res.returncode != 0:
                raise RuntimeError(f"手机下载文件失败: {(dl_res.stdout + dl_res.stderr).strip()}")

            self.log("🎉 文件极速传输完成！")

            # 4. 执行本地安装
            self.set_status("手机端正在执行系统安装 (pm install)...")
            self.log("[*] 手机正在执行本地静默安装 (pm install -r -d -t)...")
            inst_res = subprocess.run(
                ["adb", "-s", device_id, "shell", f"pm install -r -d -t {remote_tmp_apk}"],
                capture_output=True, text=True, timeout=120
            )
            output = inst_res.stdout.strip()
            self.log(f"[系统返回] {output}")

            if "Success" in output:
                self.set_status("安装成功！")
                self.log("🎉 恭喜！APK 极速安装成功！")
                messagebox.showinfo("成功", f"🎉 APK 极速安装成功！\n设备: {device_id}\n耗时仅数秒！")
            else:
                self.set_status("安装失败")
                self.log(f"❌ 安装未成功，原因: {output or inst_res.stderr.strip()}")
                if "INSTALL_FAILED_USER_RESTRICTED" in output:
                    self.log("[💡 小米系统提示] 检测到小米系统拦截 (INSTALL_FAILED_USER_RESTRICTED)！")
                    self.log("请进入手机「设置」->「更多设置」->「开发者选项」，开启「USB 安装」与「USB 调试（安全设置）」后重试！")
                messagebox.showerror("安装失败", f"安装失败！\n\n终端输出：\n{output[-300:]}")

        except Exception as e:
            self.set_status("安装异常")
            self.log(f"[异常] 极速安装过程出错: {e}")
            messagebox.showerror("异常", f"运行异常: {e}")
        finally:
            stop_http_server(httpd)
            # 清理手机端临时文件
            try:
                subprocess.run(["adb", "-s", device_id, "shell", f"rm -f {remote_tmp_apk}"], capture_output=True, timeout=5)
            except Exception:
                pass
            self.btn_install.config(state="normal")
            self.btn_refresh.config(state="normal")
            self.set_status("就绪")

    # -----------------------------------------------------------------------
    # 标准 ADB 流式安装引擎
    # -----------------------------------------------------------------------
    def _standard_install_worker(self, device_id: str, apk: str):
        try:
            self.set_status("正在通过标准 ADB 流式安装...")
            custom_args = shlex.split(self.install_args.get().strip())
            cmd = ["adb", "-s", device_id, "install"] + custom_args + [apk]

            self.log("=" * 50)
            self.log(f"🚀 [标准 ADB 模式] 执行命令: {' '.join(cmd)}")
            self.log(f"目标设备: {device_id} ({'无线设备' if ':' in device_id else '有线设备'})")
            self.log("正在安装，请稍候...")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            full_output = []
            for line in process.stdout:
                line_clean = line.rstrip()
                self.log(line_clean)
                full_output.append(line_clean)

            process.wait()
            output_str = "\n".join(full_output)

            if "Success" in output_str:
                self.set_status("安装成功！")
                self.log("🎉 安装成功！")
                messagebox.showinfo("成功", f"APK 安装成功！\n设备: {device_id}")
            else:
                self.set_status("安装失败")
                self.log("❌ 安装失败，请检查上方日志返回的错误。")
                if "INSTALL_FAILED_USER_RESTRICTED" in output_str:
                    self.log("[💡 小米系统提示] 检测到小米系统拦截 (INSTALL_FAILED_USER_RESTRICTED)！")
                    self.log("请进入手机「设置」->「更多设置」->「开发者选项」，开启「USB 安装」与「USB 调试（安全设置）」后重试！")
                messagebox.showerror("安装失败", f"安装失败！\n\n终端输出：\n{output_str[-300:]}")

        except Exception as e:
            self.set_status("安装异常")
            self.log(f"[异常] 安装过程中发生错误: {str(e)}")
            messagebox.showerror("异常", f"运行异常: {str(e)}")
        finally:
            self.btn_install.config(state="normal")
            self.btn_refresh.config(state="normal")
            self.set_status("就绪")

    def get_screenshot_target_path(self) -> Path:
        base_dir = Path(__file__).resolve().parent / "screenshots"
        custom_name = self.screenshot_filename.get().strip()

        if custom_name:
            if not custom_name.lower().endswith(".png"):
                custom_name += ".png"
            p = Path(custom_name)
            if p.is_absolute() or len(p.parts) > 1:
                return p
            return base_dir / custom_name
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return base_dir / f"screenshot_{timestamp}.png"

    def start_screenshot_thread(self):
        device_id = self.get_clean_device_id()
        if not device_id:
            messagebox.showwarning("警告", "请先选择一个有效的已连接设备！")
            return

        self.btn_screenshot.config(state="disabled")
        self.btn_refresh.config(state="disabled")

        def _worker():
            try:
                target_file = self.get_screenshot_target_path()
                self.log("=" * 50)
                self.log(f"📸 正在从设备 {device_id} 获取屏幕截图...")
                success, msg = capture_device_screenshot(device_id, target_file)
                if success:
                    size_kb = target_file.stat().st_size / 1024
                    self.log(f"🎉 截图成功！文件大小: {size_kb:.1f} KB")
                    self.log(f"保存路径: {target_file.resolve()}")
                    messagebox.showinfo("截图成功", f"屏幕截图已保存至:\n{target_file.resolve()}\n大小: {size_kb:.1f} KB")
                else:
                    self.log(f"❌ {msg}")
                    messagebox.showerror("截图失败", f"截图执行失败！\n\n{msg}")
            except Exception as e:
                self.log(f"[异常] 截图异常: {e}")
            finally:
                self.btn_screenshot.config(state="normal")
                self.btn_refresh.config(state="normal")

        threading.Thread(target=_worker, daemon=True).start()

    def open_screenshot_dir(self):
        target_dir = (Path(__file__).resolve().parent / "screenshots").resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(target_dir))
            self.log(f"[提示] 已在文件资源管理器中打开截图目录: {target_dir}")
        except Exception as e:
            self.log(f"[提示] 截图目录为: {target_dir} ({e})")


# ---------------------------------------------------------------------------
# 7. 命令行 (CLI) 自动模式支持
# ---------------------------------------------------------------------------
def run_cli_screenshot(custom_name: str = "", out_dir: str = "screenshots", target_device: str = ""):
    print("=== [Automated ADB Screencap] ===")
    devices = parse_adb_devices()
    online_devices = [d["serial"] for d in devices if d["status"] == "device"]

    if target_device:
        device = target_device
    elif online_devices:
        device = online_devices[0]
    else:
        print("[ERROR] No online ADB device detected! Connect phone via USB or Wi-Fi debugging.")
        sys.exit(1)

    base_dir = Path(out_dir).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    if custom_name.strip():
        fname = custom_name.strip()
        if not fname.lower().endswith(".png"):
            fname += ".png"
        p = Path(fname)
        target_path = p if p.is_absolute() or len(p.parts) > 1 else base_dir / fname
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_path = base_dir / f"screenshot_{timestamp}.png"

    print(f"[*] Target device: {device} ({'Wireless' if ':' in device else 'Wired'})")
    print(f"[*] Capturing to: {target_path}")
    ok, msg = capture_device_screenshot(device, target_path)
    if ok:
        print(f"[SUCCESS] {msg} ({target_path.stat().st_size / 1024:.1f} KB)")
    else:
        print(f"[ERROR] {msg}")
        sys.exit(1)


def run_cli_fast_install(apk_path: str, device: str) -> bool:
    remote_tmp_apk = "/data/local/tmp/_fast_install_temp.apk"
    apk_p = Path(apk_path).resolve()
    apk_dir = apk_p.parent
    apk_name = apk_p.name

    downloader = detect_downloader(device)
    if not downloader:
        print("[WARN] No curl/wget on device, falling back to standard install...")
        return False

    httpd, port = start_http_server(apk_dir)
    phone_ip = device.split(":")[0] if ":" in device else (get_device_wifi_ip(device) or "192.168.1.1")
    local_ip = get_local_ip(phone_ip)
    download_url = f"http://{local_ip}:{port}/{urllib.parse.quote(apk_name)}"
    print(f"[*] LAN Fast HTTP node: {download_url}")

    try:
        if "curl" in downloader:
            dl_cmd = f"{downloader} -fSL --connect-timeout 8 -o {remote_tmp_apk} '{download_url}'"
        else:
            dl_cmd = f"{downloader} -O {remote_tmp_apk} '{download_url}'"

        print(f"[*] Downloading APK on device via {downloader} ...")
        res = subprocess.run(["adb", "-s", device, "shell", dl_cmd], timeout=180)
        stop_http_server(httpd)
        httpd = None

        if res.returncode != 0:
            print("[ERROR] Download on device failed.")
            return False

        print("[*] Installing on device: pm install -r -d -t ...")
        res = subprocess.run(["adb", "-s", device, "shell", f"pm install -r -d -t {remote_tmp_apk}"], capture_output=True, text=True, timeout=120)
        out = res.stdout.strip()
        print(f"[RESULT] {out}")
        return "Success" in out
    except Exception as e:
        print(f"[ERROR] Fast install error: {e}")
        return False
    finally:
        stop_http_server(httpd)
        subprocess.run(["adb", "-s", device, "shell", f"rm -f {remote_tmp_apk}"], capture_output=True)


def run_cli_install(apk_path: str, target_device: str = "", force_fast: bool = False, force_standard: bool = False):
    print(f"=== [Automated ADB Installer] Target APK: {apk_path} ===")
    devices = parse_adb_devices()
    online_devices = [d["serial"] for d in devices if d["status"] == "device"]

    if target_device:
        device = target_device
    elif online_devices:
        device = online_devices[0]
    else:
        print("[ERROR] No online ADB device detected! Connect phone via USB or Wi-Fi debugging.")
        sys.exit(1)

    is_wireless = ":" in device
    print(f"[*] Target device: {device} ({'Wireless' if is_wireless else 'Wired'})")

    use_fast = (force_fast or (is_wireless and not force_standard))

    if use_fast:
        print("[*] Mode: Blazing LAN HTTP Fast Install")
        success = run_cli_fast_install(apk_path, device)
        if success:
            print(f"\n[SUCCESS] Successfully fast-installed {apk_path} on {device}!")
            return
        print("[WARN] Fast install failed or unsupported, falling back to standard adb install...")

    # 标准安装
    print("[*] Mode: Standard ADB Stream Install")
    cmd = ["adb", "-s", device, "install", "-r", "--no-incremental", apk_path]
    print(f"[*] Running: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        print(line.rstrip())
    proc.wait()
    if proc.returncode == 0:
        print(f"\n[SUCCESS] Successfully installed {apk_path} on {device}!")
    else:
        print(f"\n[ERROR] ADB installation failed with exit code {proc.returncode}")
        sys.exit(proc.returncode)


def run_cli_connect(ip: str, port: str = "5555"):
    addr = ip if ":" in ip else f"{ip}:{port}"
    print(f"=== Connecting to wireless device: {addr} ===")
    res = subprocess.run(["adb", "connect", addr], capture_output=True, text=True)
    out = (res.stdout + res.stderr).strip()
    print(out)
    if "connected to" in out.lower():
        parts = addr.split(":", 1)
        record_history_ip_port(parts[0], parts[1] if len(parts) > 1 else "5555")
        print("[SUCCESS] Connected successfully!")
    else:
        sys.exit(1)


def run_cli_disconnect(addr: str = ""):
    cmd = ["adb", "disconnect"]
    if addr:
        cmd.append(addr)
    res = subprocess.run(cmd, capture_output=True, text=True)
    print((res.stdout + res.stderr).strip())


def run_cli_tcpip(port: str = "5555", target_device: str = ""):
    devices = parse_adb_devices()
    usb_devices = [d["serial"] for d in devices if not d["is_wireless"] and d["status"] == "device"]
    if target_device:
        device = target_device
    elif usb_devices:
        device = usb_devices[0]
    else:
        print("[ERROR] No USB connected online device found to switch to TCP/IP mode.")
        sys.exit(1)

    ip = get_device_wifi_ip(device)
    print(f"[*] Device {device} Wi-Fi IP: {ip or 'Unknown'}")
    print(f"[*] Running: adb -s {device} tcpip {port}")
    subprocess.run(["adb", "-s", device, "tcpip", port], check=True)
    if ip:
        target = f"{ip}:{port}"
        time.sleep(1.5)
        print(f"[*] Auto-connecting to {target} ...")
        res = subprocess.run(["adb", "connect", target], capture_output=True, text=True)
        print((res.stdout + res.stderr).strip())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ADB APK 极速安装与设备管理 (支持有线/无线、小米插线转无线及局域网直传)")
    parser.add_argument("--apk", type=str, help="APK 路径（若指定且带 --auto 则直接安装）")
    parser.add_argument("--auto", action="store_true", help="命令行自动安装模式，不启动图形界面")
    parser.add_argument("--fast", action="store_true", help="强制启用局域网 HTTP 极速直传模式")
    parser.add_argument("--standard", action="store_true", help="强制启用标准 ADB 流式安装")
    parser.add_argument("--device", type=str, default="", help="指定目标设备 serial 或 IP:PORT")
    parser.add_argument("--screenshot", action="store_true", help="从已连接设备截取屏幕保存到本地（默认同名覆盖）")
    parser.add_argument("--name", type=str, default="", help="截图文件名（可选，默认带时间戳变量）")
    parser.add_argument("--out-dir", type=str, default="screenshots", help="截图保存目录（默认 screenshots）")
    parser.add_argument("--connect", type=str, help="连接无线调试设备 (例如 192.168.1.100:5555)")
    parser.add_argument("--ip", type=str, help="无线设备 IP 地址 (搭配 --port 使用)")
    parser.add_argument("--port", type=str, default="5555", help="无线设备端口 (默认 5555)")
    parser.add_argument("--tcpip", nargs="?", const="5555", help="将当前 USB 设备切换为 TCP/IP 无线监听端口 (默认 5555)")
    parser.add_argument("--disconnect", nargs="?", const="", help="断开无线设备连接 (可选指定 IP:PORT，默认断开全部)")
    args = parser.parse_args()

    if args.connect:
        run_cli_connect(args.connect)
    elif args.ip:
        run_cli_connect(args.ip, port=args.port)
    elif args.tcpip is not None:
        run_cli_tcpip(port=args.tcpip, target_device=args.device)
    elif args.disconnect is not None:
        run_cli_disconnect(args.disconnect)
    elif args.screenshot:
        run_cli_screenshot(custom_name=args.name, out_dir=args.out_dir, target_device=args.device)
    elif args.auto:
        target_apk = args.apk
        if not target_apk:
            build_apks = list(Path("build").glob("*.apk"))
            if build_apks:
                target_apk = str(sorted(build_apks, key=lambda p: p.stat().st_mtime, reverse=True)[0])
        if not target_apk or not Path(target_apk).exists():
            print(f"[ERROR] APK not found: {target_apk}")
            sys.exit(1)
        run_cli_install(target_apk, target_device=args.device, force_fast=args.fast, force_standard=args.standard)
    else:
        root = tk.Tk()
        app = ApkInstallerApp(root)
        if args.apk and Path(args.apk).exists():
            app.apk_path.set(str(Path(args.apk).resolve()))
        root.mainloop()