import os
import sys
import shlex
import subprocess
import threading
from datetime import datetime
from pathlib import Path

# Automatically append toolchain adb path if available
_toolchain_adb = Path(__file__).resolve().parent / "toolchain" / "android-sdk" / "platform-tools"
if _toolchain_adb.is_dir() and str(_toolchain_adb) not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{_toolchain_adb}{os.pathsep}{os.environ.get('PATH', '')}"

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText


class ApkInstallerApp:

    def __init__(self, root):
        self.root = root
        self.root.title("ADB APK 安装与截图工具")
        self.root.geometry("640x580")
        self.root.minsize(520, 450)

        # 变量绑定
        self.selected_device = tk.StringVar()
        self.apk_path = tk.StringVar()
        # 注意：adb 官方参数为 --no-incremental（此处做成可编辑输入框，默认填入）
        self.install_args = tk.StringVar(value="-r --no-incremental")
        self.screenshot_filename = tk.StringVar(value="")

        self._create_widgets()
        self.refresh_devices()

    def _create_widgets(self):
        # 1. 设备选择区域
        dev_frame = ttk.LabelFrame(self.root, text="设备选择", padding=10)
        dev_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(dev_frame, text="目标设备:").pack(side="left", padx=5)
        self.device_combo = ttk.Combobox(
            dev_frame,
            textvariable=self.selected_device,
            state="readonly",
            width=30,
        )
        self.device_combo.pack(side="left", fill="x", expand=True, padx=5)

        self.btn_refresh = ttk.Button(
            dev_frame, text="🔄 刷新设备", command=self.refresh_devices
        )
        self.btn_refresh.pack(side="right", padx=5)

        # 2. APK 选择区域
        file_frame = ttk.LabelFrame(self.root, text="APK 文件", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)

        ttk.Entry(file_frame, textvariable=self.apk_path).pack(
            side="left", fill="x", expand=True, padx=5
        )
        ttk.Button(
            file_frame, text="📂 选择 APK", command=self.browse_apk
        ).pack(side="right", padx=5)

        # 3. 安装参数区域
        param_frame = ttk.LabelFrame(self.root, text="安装参数", padding=10)
        param_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(param_frame, text="额外参数:").pack(side="left", padx=5)
        ttk.Entry(param_frame, textvariable=self.install_args).pack(
            side="left", fill="x", expand=True, padx=5
        )

        # 4. 操作按钮
        self.btn_install = ttk.Button(
            self.root, text="🚀 开始安装", command=self.start_install_thread
        )
        self.btn_install.pack(fill="x", padx=10, pady=5)

        # 5. 设备截图区域
        shot_frame = ttk.LabelFrame(self.root, text="设备截图", padding=10)
        shot_frame.pack(fill="x", padx=10, pady=5)

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
        ).pack(anchor="w", padx=5, pady=(4, 0))

        # 6. 日志输出区域
        log_frame = ttk.LabelFrame(self.root, text="执行日志", padding=5)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_text = ScrolledText(
            log_frame, wrap="word", height=10, bg="#1e1e1e", fg="#d4d4d4"
        )
        self.log_text.pack(fill="both", expand=True)

    def log(self, message):
        """向界面日志窗口输出内容"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def refresh_devices(self):
        """刷新 adb devices 列表"""
        try:
            res = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            lines = res.stdout.strip().splitlines()
            devices = []
            # 过滤第一行 "List of devices attached"
            for line in lines[1:]:
                parts = line.strip().split()
                if len(parts) >= 2:
                    serial, status = parts[0], parts[1]
                    devices.append(f"{serial} ({status})")

            self.device_combo["values"] = devices
            if devices:
                self.device_combo.current(0)
                self.log(f"[提示] 发现 {len(devices)} 台设备")
            else:
                self.selected_device.set("")
                self.log("[提示] 未检测到任何已连接的设备")
        except FileNotFoundError:
            self.log("[错误] 未找到 adb 命令，请确保已安装 ADB 并配置了环境变量！")
            messagebox.showerror("错误", "系统找不到 adb 命令，请检查环境变量！")

    def browse_apk(self):
        """打开文件选择器选择 APK 文件"""
        file_selected = filedialog.askopenfilename(
            title="选择要安装的 APK",
            filetypes=[("APK 文件", "*.apk"), ("所有文件", "*.*")],
        )
        if file_selected:
            self.apk_path.set(file_selected)

    def get_clean_device_id(self):
        """从下拉选项中提取设备 serial"""
        val = self.selected_device.get().strip()
        if not val:
            return None
        return val.split()[0]

    def start_install_thread(self):
        """启动后台线程进行安装，防止界面无响应"""
        device_id = self.get_clean_device_id()
        apk = self.apk_path.get().strip()

        if not device_id:
            messagebox.showwarning("警告", "请先选择一个有效的设备！")
            return

        if not apk or not os.path.exists(apk):
            messagebox.showwarning("警告", "请选择有效的 APK 文件路径！")
            return

        # 禁用按钮，避免重复点击
        self.btn_install.config(state="disabled")
        self.btn_refresh.config(state="disabled")

        # 开启独立线程安装
        thread = threading.Thread(
            target=self._install_worker, args=(device_id, apk)
        )
        thread.daemon = True
        thread.start()

    def _install_worker(self, device_id, apk):
        try:
            # 解析命令行参数
            custom_args = shlex.split(self.install_args.get().strip())
            cmd = ["adb", "-s", device_id, "install"] + custom_args + [apk]

            self.log("=" * 50)
            self.log(f"执行命令: {' '.join(cmd)}")
            self.log("正在安装，请稍候...")

            # 实时捕获子进程输出
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

            # 判断安装结果
            if "Success" in output_str:
                self.log("🎉 安装成功！")
                messagebox.showinfo("成功", f"APK 安装成功！\n设备: {device_id}")
            else:
                self.log("❌ 安装失败，请检查上方日志返回的错误。")
                messagebox.showerror(
                    "安装失败", f"安装失败！\n\n终端输出：\n{output_str[-300:]}"
                )

        except Exception as e:
            self.log(f"[异常] 安装过程中发生错误: {str(e)}")
            messagebox.showerror("异常", f"运行异常: {str(e)}")
        finally:
            # 恢复按钮状态
            self.btn_install.config(state="normal")
            self.btn_refresh.config(state="normal")

    def get_screenshot_target_path(self) -> Path:
        """根据输入框计算最终截图保存路径，默认同名覆盖"""
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
        """启动后台线程进行截图，防止界面无响应"""
        device_id = self.get_clean_device_id()
        if not device_id:
            messagebox.showwarning("警告", "请先选择一个有效的已连接设备！")
            return

        self.btn_screenshot.config(state="disabled")
        self.btn_refresh.config(state="disabled")

        thread = threading.Thread(
            target=self._screenshot_worker, args=(device_id,)
        )
        thread.daemon = True
        thread.start()

    def _screenshot_worker(self, device_id):
        try:
            target_file = self.get_screenshot_target_path()
            self.log("=" * 50)
            self.log(f"📸 正在从设备 {device_id} 获取屏幕截图...")
            self.log(f"目标保存路径: {target_file.resolve()}")

            success, msg = capture_device_screenshot(device_id, target_file)
            if success:
                size_kb = target_file.stat().st_size / 1024
                self.log(f"🎉 截图成功！文件大小: {size_kb:.1f} KB")
                self.log(f"保存路径: {target_file.resolve()}")
                messagebox.showinfo(
                    "截图成功",
                    f"屏幕截图已保存至:\n{target_file.resolve()}\n大小: {size_kb:.1f} KB",
                )
            else:
                self.log(f"❌ {msg}")
                messagebox.showerror("截图失败", f"截图执行失败！\n\n{msg}")

        except Exception as e:
            self.log(f"[异常] 截图过程中发生错误: {str(e)}")
            messagebox.showerror("异常", f"截图异常: {str(e)}")
        finally:
            self.btn_screenshot.config(state="normal")
            self.btn_refresh.config(state="normal")

    def open_screenshot_dir(self):
        """打开截图存放目录"""
        target_dir = (Path(__file__).resolve().parent / "screenshots").resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(target_dir))
            self.log(f"[提示] 已在文件资源管理器中打开截图目录: {target_dir}")
        except Exception as e:
            self.log(f"[提示] 截图目录为: {target_dir} ({e})")


def capture_device_screenshot(device_id: str, output_file: Path) -> tuple[bool, str]:
    """
    通过 ADB 从设备截取当前屏幕并保存到本地 output_file（默认同名覆盖）。
    优先采用高效二进制流 (exec-out screencap -p)，若失败则自动回退至 (shell screencap -> pull -> rm)。
    """
    output_file = Path(output_file).resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. 优先尝试 exec-out screencap -p (秒级快速抓取)
    try:
        cmd = ["adb", "-s", device_id, "exec-out", "screencap", "-p"]
        res = subprocess.run(cmd, capture_output=True, timeout=12)
        if res.returncode == 0 and res.stdout.startswith(b"\x89PNG\r\n\x1a\n"):
            output_file.write_bytes(res.stdout)
            return True, f"截图已保存至: {output_file}"
    except Exception:
        pass

    # 2. 回退机制: 通过设备临时存储转存并 pull
    try:
        remote_tmp = "/data/local/tmp/tftf_screencap.png"
        subprocess.run(
            ["adb", "-s", device_id, "shell", "screencap", "-p", remote_tmp],
            check=True,
            timeout=12,
        )
        subprocess.run(
            ["adb", "-s", device_id, "pull", remote_tmp, str(output_file)],
            check=True,
            timeout=12,
        )
        subprocess.run(
            ["adb", "-s", device_id, "shell", "rm", "-f", remote_tmp],
            timeout=5,
        )
        if output_file.exists() and output_file.stat().st_size > 0:
            return True, f"截图已保存至: {output_file}"
        return False, "未能从设备拉取到有效截图文件"
    except Exception as e:
        return False, f"ADB 截图执行失败: {e}"


def run_cli_screenshot(custom_name: str = "", out_dir: str = "screenshots"):
    print("=== [Automated ADB Screencap] ===")
    res = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    devices = []
    for line in res.stdout.splitlines()[1:]:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    if not devices:
        print(
            "[ERROR] No online ADB device detected! Please connect your phone with USB debugging enabled."
        )
        sys.exit(1)

    device = devices[0]
    base_dir = Path(out_dir).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    if custom_name.strip():
        fname = custom_name.strip()
        if not fname.lower().endswith(".png"):
            fname += ".png"
        p = Path(fname)
        target_path = (
            p if p.is_absolute() or len(p.parts) > 1 else base_dir / fname
        )
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_path = base_dir / f"screenshot_{timestamp}.png"

    print(f"[*] Target device: {device}")
    print(f"[*] Capturing to: {target_path}")
    ok, msg = capture_device_screenshot(device, target_path)
    if ok:
        print(f"[SUCCESS] {msg} ({target_path.stat().st_size / 1024:.1f} KB)")
    else:
        print(f"[ERROR] {msg}")
        sys.exit(1)


def run_cli_install(apk_path: str):
    print(f"=== [Automated ADB Installer] Target APK: {apk_path} ===")
    # 1. Get devices
    res = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    devices = []
    for line in res.stdout.splitlines()[1:]:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    if not devices:
        print(
            "[ERROR] No online ADB device detected! Please connect your phone with USB debugging enabled."
        )
        sys.exit(1)

    device = devices[0]
    print(f"[*] Detected device: {device}")
    cmd = ["adb", "-s", device, "install", "-r", "--no-incremental", apk_path]
    print(f"[*] Running: {' '.join(cmd)}")
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    for line in proc.stdout:
        print(line.rstrip())
    proc.wait()
    if proc.returncode == 0:
        print(f"\n[SUCCESS] Successfully installed {apk_path} on {device}!")
    else:
        print(f"\n[ERROR] ADB installation failed with exit code {proc.returncode}")
        sys.exit(proc.returncode)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ADB APK 安装与截图工具")
    parser.add_argument(
        "--apk", type=str, help="APK 路径（若指定且带 --auto 则直接安装）"
    )
    parser.add_argument(
        "--auto", action="store_true", help="命令行自动安装模式，不启动图形界面"
    )
    parser.add_argument(
        "--screenshot",
        action="store_true",
        help="从已连接设备截取屏幕保存到本地（默认同名覆盖）",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="",
        help="截图文件名（可选，默认带时间戳变量）",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="screenshots",
        help="截图保存目录（默认 screenshots）",
    )
    args = parser.parse_args()

    if args.screenshot:
        run_cli_screenshot(custom_name=args.name, out_dir=args.out_dir)
    elif args.auto:
        target_apk = args.apk
        if not target_apk:
            # Default to latest build apk
            build_apks = list(Path("build").glob("*.apk"))
            if build_apks:
                target_apk = str(
                    sorted(
                        build_apks, key=lambda p: p.stat().st_mtime, reverse=True
                    )[0]
                )
        if not target_apk or not Path(target_apk).exists():
            print(f"[ERROR] APK not found: {target_apk}")
            sys.exit(1)
        run_cli_install(target_apk)
    else:
        root = tk.Tk()
        app = ApkInstallerApp(root)
        if args.apk and Path(args.apk).exists():
            app.apk_path.set(str(Path(args.apk).resolve()))
        root.mainloop()