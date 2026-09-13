import os
import sys
import shlex
import subprocess
import threading
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
        self.root.title("ADB APK 安装工具")
        self.root.geometry("620x520")
        self.root.minsize(500, 400)

        # 变量绑定
        self.selected_device = tk.StringVar()
        self.apk_path = tk.StringVar()
        # 注意：adb 官方参数为 --no-incremental（此处做成可编辑输入框，默认填入）
        self.install_args = tk.StringVar(value="-r --no-incremental")

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

        # 5. 日志输出区域
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
        print("[ERROR] No online ADB device detected! Please connect your phone with USB debugging enabled.")
        sys.exit(1)
    
    device = devices[0]
    print(f"[*] Detected device: {device}")
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


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ADB APK 安装工具")
    parser.add_argument("--apk", type=str, help="APK 路径（若指定且带 --auto 则直接安装）")
    parser.add_argument("--auto", action="store_true", help="命令行自动安装模式，不启动图形界面")
    args = parser.parse_args()

    if args.auto:
        target_apk = args.apk
        if not target_apk:
            # Default to latest build apk
            build_apks = list(Path("build").glob("*.apk"))
            if build_apks:
                target_apk = str(sorted(build_apks, key=lambda p: p.stat().st_mtime, reverse=True)[0])
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