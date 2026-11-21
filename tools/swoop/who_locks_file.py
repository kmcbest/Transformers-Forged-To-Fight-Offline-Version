import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import ctypes
from ctypes import wintypes
from pathlib import Path

# Restart Manager API
rstrtmgr = ctypes.windll.rstrtmgr

CCH_RM_SESSION_KEY = 32
CCH_RM_MAX_APP_NAME = 255
CCH_RM_MAX_SVC_NAME = 63

class RM_UNIQUE_PROCESS(ctypes.Structure):
    _fields_ = [
        ("dwProcessId", wintypes.DWORD),
        ("ProcessStartTime", wintypes.FILETIME)
    ]

class RM_PROCESS_INFO(ctypes.Structure):
    _fields_ = [
        ("Process", RM_UNIQUE_PROCESS),
        ("strAppName", wintypes.WCHAR * (CCH_RM_MAX_APP_NAME + 1)),
        ("strServiceShortName", wintypes.WCHAR * (CCH_RM_MAX_SVC_NAME + 1)),
        ("ApplicationType", wintypes.DWORD),
        ("AppStatus", wintypes.DWORD),
        ("TSSessionId", wintypes.DWORD),
        ("bRestartable", wintypes.BOOL)
    ]

target = str(Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Temp\UnityLockfile").resolve())

session_handle = wintypes.DWORD()
session_key = (wintypes.WCHAR * (CCH_RM_SESSION_KEY + 1))()

res = rstrtmgr.RmStartSession(ctypes.byref(session_handle), 0, session_key)
if res != 0:
    print(f"RmStartSession failed with error {res}")
    sys.exit(1)

try:
    c_target = wintypes.LPCWSTR(target)
    res = rstrtmgr.RmRegisterResources(session_handle, 1, ctypes.byref(c_target), 0, None, 0, None)
    if res != 0:
        print(f"RmRegisterResources failed with error {res}")
        sys.exit(1)

    n_proc_info_needed = wintypes.UINT(0)
    n_proc_info = wintypes.UINT(0)
    reboot_reasons = wintypes.DWORD()

    res = rstrtmgr.RmGetList(session_handle, ctypes.byref(n_proc_info_needed), ctypes.byref(n_proc_info), None, ctypes.byref(reboot_reasons))
    if res == 234: # ERROR_MORE_DATA
        proc_infos = (RM_PROCESS_INFO * n_proc_info_needed.value)()
        n_proc_info.value = n_proc_info_needed.value
        res = rstrtmgr.RmGetList(session_handle, ctypes.byref(n_proc_info_needed), ctypes.byref(n_proc_info), proc_infos, ctypes.byref(reboot_reasons))
        if res == 0:
            for i in range(n_proc_info.value):
                pi = proc_infos[i]
                print(f"PID: {pi.Process.dwProcessId}, App: {pi.strAppName}")
        else:
            print(f"RmGetList failed with {res}")
    elif res == 0:
        print("No processes locking the file.")
    else:
        print(f"RmGetList returned {res}")
finally:
    rstrtmgr.RmEndSession(session_handle)
