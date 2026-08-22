#!/usr/bin/env python3
"""Build a stock-device APK for a local fake server.

The emulator setup rewrites /system/etc/hosts and the system CA store, which
requires root.  A retail phone cannot do either.  This builder instead:

* rewrites the game's known backend hosts to a configurable server host,
  scheme, and port (defaulting to https on 8443).  Use a laptop LAN address
  for cable-free play, or the default 127.0.0.1 with adb reverse for the
  original USB setup.  --scheme http and --server-port support a plain-HTTP
  local server.
* embeds the repository's current runtime hook for the chosen ABI.  The source
  APK is a convenient build input, but its bundled hook may predate later
  gameplay fixes.

The APK ships native libraries for both arm64-v8a and armeabi-v7a, so --abi
picks which one the build targets.  arm64-v8a is the default and is the better
tested path; armeabi-v7a exists for 32-bit devices and 32-bit emulators.  By
default the other ABI's libraries are dropped, because Android prefers the
64-bit ones whenever they are present and would otherwise load the unpatched
library and silently ignore the whole offline build.

The original target SDK is preserved. The bundled native patches handle the
fake server certificate; lowering the target SDK causes modern Play Protect
to reject the installation.

The resulting APK must be signed after this script finishes.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import struct
import zipfile
from pathlib import Path

# Server/ is intentionally a script directory rather than a Python package.  A
# plain import works both for ``python3 Server/build_phone_apk.py`` and for the
# unittest suite, which inserts this directory on sys.path before importing us.
import export_payload


METADATA = "assets/bin/Data/Managed/Metadata/global-metadata.dat"
SPARX_MANIFEST = "res/raw/sparxmanifest"
ENDPOINT_CONFIG = "assets/bin/Data/e1917cd7a6bdb4492a247b8f758df2ae"
ARM64 = "arm64-v8a"
ARMV7 = "armeabi-v7a"
NATIVEHOOK = Path(__file__).resolve().parents[1] / "tools/nativehook"
# (hook source built for this ABI, expected ELF class, expected e_machine)
ABIS = {
    ARM64: (NATIVEHOOK / "libdothook.so", 2, 183),                    # ELFCLASS64, EM_AARCH64
    ARMV7: (NATIVEHOOK / "libdothook-armeabi-v7a.so", 1, 40),         # ELFCLASS32, EM_ARM
}
ARM64_HOOK = f"lib/{ARM64}/libdothook.so"
CURRENT_HOOK = ABIS[ARM64][0]
PAYLOAD_ASSET = "assets/tftf_offline_payload.bin"


def hook_entry(abi: str) -> str:
    return f"lib/{abi}/libdothook.so"


def il2cpp_entry(abi: str) -> str:
    return f"lib/{abi}/libil2cpp.so"


def check_elf(data: bytes, abi: str, path: Path, description: str) -> None:
    """Reject a native library built for the wrong ABI.

    Dropping an arm64 hook into the armeabi-v7a slot produces an APK that
    installs and launches, then silently never loads the hook, which looks
    exactly like the game hanging at login for unrelated reasons.
    """
    _, want_class, want_machine = ABIS[abi]
    if not data.startswith(b"\x7fELF"):
        raise ValueError(f"{description} is not an ELF library: {path}")
    elf_class = data[4]
    machine = struct.unpack_from("<H", data, 18)[0]
    if elf_class != want_class or machine != want_machine:
        raise ValueError(
            f"{description} {path} is ELF class {elf_class}/machine {machine}, "
            f"but {abi} needs class {want_class}/machine {want_machine}"
        )


def check_hook(data: bytes, abi: str, path: Path, *, bundle_server: bool = False) -> None:
    check_elf(data, abi, path, "runtime hook")
    if bundle_server and PAYLOAD_ASSET.encode() not in data:
        raise ValueError(
            f"runtime hook {path} was built without the in-app server "
            f"(no {PAYLOAD_ASSET} reference); rebuild it with tools/nativehook/inapk_server.c"
        )


DEFAULT_SERVER_HOST = "127.0.0.1"
HOSTNAME_RE = re.compile(
    r"(?=.{1,253}\Z)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\Z"
)


def validate_server_host(value: str) -> str:
    """Accept a bare IPv4 address or DNS name, never a URL/port/path."""
    value = value.strip()
    if not value or any(char in value for char in "/:[]"):
        raise argparse.ArgumentTypeError(
            "server host must be a bare IPv4 address or DNS name (no scheme, port, or path)"
        )
    try:
        ipaddress.IPv4Address(value)
    except ipaddress.AddressValueError:
        # A dotted decimal typo (for example 192.168.0.999) must not slip
        # through as a syntactically valid DNS name.
        if re.fullmatch(r"[0-9.]+", value) or not HOSTNAME_RE.fullmatch(value):
            raise argparse.ArgumentTypeError(f"invalid server host: {value!r}")
    return value


def validate_server_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid server port: {value!r}") from None
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("server port must be in the range 1..65535")
    return port


def literal_replacements(
    server_host: str, server_port: int = 8443
) -> tuple[tuple[bytes, bytes], ...]:
    # Game code prepends these three bare-host literals with its own scheme;
    # thus --scheme http would still dial them as https. This is accepted:
    # Server/logs/*.log shows a full offline boot never requests them.
    host = server_host.encode("ascii")
    port = str(server_port).encode("ascii")
    return (
        (b"tf-odr.mcoc-cdn.cn", host + b":" + port),
        (b"tf-static.mcoc-cdn.cn", host + b":" + port),
        (b"words-express.tf-cdn.net", host + b":" + port),
        (b"wss://gametalk.sparx.io:30443", b"wss://" + host + b":30443"),
    )


def patch_metadata(
    metadata: bytes, server_host: str, server_port: int = 8443
) -> tuple[bytes, list[str]]:
    """Rewrite IL2CPP string literals and their table lengths without shifting data."""
    out = bytearray(metadata)
    literal_offset, literal_count, data_offset, _ = struct.unpack_from("<4I", out, 8)
    changed: list[str] = []
    pending = dict(literal_replacements(server_host, server_port))
    for entry in range(literal_offset, literal_offset + literal_count, 8):
        length, index = struct.unpack_from("<II", out, entry)
        value_start = data_offset + index
        value = bytes(out[value_start : value_start + length])
        replacement = pending.pop(value, None)
        if replacement is None:
            continue
        if len(replacement) > length:
            raise ValueError(f"replacement is longer than literal: {value!r}")
        out[value_start : value_start + len(replacement)] = replacement
        struct.pack_into("<I", out, entry, len(replacement))
        changed.append(value.decode())
    if pending:
        missing = ", ".join(value.decode() for value in pending)
        raise ValueError(f"expected string literals not found: {missing}")
    return bytes(out), changed


def patch_sparx_manifest(
    data: bytes, server_host: str, scheme: str = "https", server_port: int = 8443
) -> bytes:
    old = b"https://tform-0901-hzlhiniyfcwf.tf-cdn.net"
    if data.count(old) != 1:
        raise ValueError("unexpected Sparx manifest endpoint count")
    return data.replace(old, f"{scheme}://{server_host}:{server_port}".encode("ascii"))


def patch_endpoint_config(
    data: bytes, server_host: str, scheme: str = "https", server_port: int = 8443
) -> bytes:
    """Patch fixed-size Unity TextAsset JSON, preserving its serialized byte length."""
    old = b'{"Default":{"Prod":"https://tform-0901-hzlhiniyfcwf.tf-cdn.net"}}'
    new = f'{{"Default":{{"Prod":"{scheme}://{server_host}:{server_port}"}}}}'.encode("ascii")
    if data.count(old) != 1:
        raise ValueError("unexpected Unity endpoint config count")
    if len(new) > len(old):
        raise ValueError("server host is too long for the fixed-size Unity endpoint config")
    return data.replace(old, new + b" " * (len(old) - len(new)))


def build(
    source: Path,
    destination: Path,
    server_host: str = DEFAULT_SERVER_HOST,
    abi: str = ARM64,
    keep_other_abi: bool = False,
    patched_il2cpp: Path | None = None,
    scheme: str = "https",
    server_port: int = 8443,
    *,
    bundle_server: bool = False,
) -> list[str]:
    if source.resolve() == destination.resolve():
        raise ValueError("destination must differ from source; the original APK is preserved")
    if bundle_server and scheme != "http":
        raise ValueError("bundled server requires --scheme http")
    if bundle_server and server_host != "127.0.0.1":
        raise ValueError("bundled server binds loopback only; --server-host must be 127.0.0.1")
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = export_payload.build_payload(server_port) if bundle_server else None
    hook_path = ABIS[abi][0]
    if not hook_path.is_file():
        raise ValueError(f"current runtime hook is missing: {hook_path}")
    hook = hook_path.read_bytes()
    # A hook built without inapk_server.c installs and launches, then hangs at
    # login with no listener; reject that bundled-server failure loudly.
    check_hook(hook, abi, hook_path, bundle_server=bundle_server)
    replacement_il2cpp = None
    if patched_il2cpp is not None:
        if not patched_il2cpp.is_file():
            raise ValueError(f"patched libil2cpp is missing: {patched_il2cpp}")
        replacement_il2cpp = patched_il2cpp.read_bytes()
        check_elf(replacement_il2cpp, abi, patched_il2cpp, "patched libil2cpp")
        if b"libdothook.so" not in replacement_il2cpp:
            raise ValueError(
                f"patched libil2cpp does not reference libdothook.so: {patched_il2cpp}"
            )

    wanted_hook = hook_entry(abi)
    wanted_il2cpp = il2cpp_entry(abi)
    other_abi_prefix = f"lib/{ARMV7 if abi == ARM64 else ARM64}/"

    with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(destination, "w") as zout:
        names = set(zin.namelist())
        for required in (
            "AndroidManifest.xml", METADATA, SPARX_MANIFEST, ENDPOINT_CONFIG,
            wanted_il2cpp,
        ):
            if required not in names:
                raise ValueError(f"APK is missing {required}")

        changed_hosts: list[str] = []
        char_bundle_data = None
        for info in zin.infolist():
            # Old JAR signatures are invalid after modification. apksigner will add new ones.
            upper = info.filename.upper()
            if upper.startswith("META-INF/") and upper.endswith((".SF", ".RSA", ".DSA", ".EC", "MANIFEST.MF")):
                continue
            if not keep_other_abi and info.filename.startswith(other_abi_prefix):
                continue
            # Rebuilding a bundled APK must replace the payload, rather than
            # retaining a stale duplicate asset that Unity might mmap first.
            if bundle_server and info.filename == PAYLOAD_ASSET:
                continue
            data = zin.read(info)
            if info.filename == "assets/assetpack/characters/characters.assetbundle":
                char_bundle_data = data
            if info.filename == METADATA:
                data, metadata_hosts = patch_metadata(data, server_host, server_port)
                changed_hosts.extend(metadata_hosts)
            elif info.filename == SPARX_MANIFEST:
                data = patch_sparx_manifest(data, server_host, scheme, server_port)
                changed_hosts.append("tform-0901-hzlhiniyfcwf.tf-cdn.net")
            elif info.filename == ENDPOINT_CONFIG:
                data = patch_endpoint_config(data, server_host, scheme, server_port)
            elif info.filename == wanted_hook:
                data = hook
            elif info.filename == wanted_il2cpp and replacement_il2cpp is not None:
                data = replacement_il2cpp
            elif info.filename == "assets/assetpack/characters/moves.assetbundle":
                mpath = Path("assets_netflix/moves.assetbundle")
                if mpath.exists():
                    data = mpath.read_bytes()
            elif info.filename == "assets/assetpack/characters_procedural_odr/character_anim_procedural.assetbundle":
                panimpath = Path("assets_netflix/character_anim_procedural.assetbundle")
                if panimpath.exists():
                    data = panimpath.read_bytes()
            elif info.filename == "assets/assetpack/characters_procedural_odr/character_audio_procedural.assetbundle":
                paudiopath = Path("assets_netflix/character_audio_procedural.assetbundle")
                if paudiopath.exists():
                    data = paudiopath.read_bytes()
            elif info.filename == "assets/assetpack/characters_procedural_odr/character_matinee_procedural.assetbundle":
                pmatpath = Path("assets_netflix/character_matinee_procedural.assetbundle")
                if pmatpath.exists():
                    data = pmatpath.read_bytes()
            elif info.filename == "assets/packs.txt":
                try:
                    pdict = json.loads(data.decode("utf-8"))
                    packs = pdict.get("packs", {})
                    for pkey in [
                        "chromia_gs_kabam_odr",
                        "deadend_gs_deluxe2015_odr",
                        "optimusprime_gs_v_odr",
                        "starscream_gs_odr",
                    ]:
                        packs[pkey] = pkey
                    pdict["packs"] = packs
                    data = json.dumps(pdict, indent=4).encode("utf-8")
                except Exception:
                    pass
            elif info.filename == "assets/portraits_odr/toc.txt":
                try:
                    ptoc = json.loads(data.decode("utf-8"))
                    flist = ptoc.get("files", [])
                    for pentry in [
                        "portraits/portrait_chromia_gs_large.png",
                        "portraits/portrait_chromia_gs_small.jpg",
                        "portraits/portrait_deadend_gs_large.png",
                        "portraits/portrait_deadend_gs_small.jpg",
                    ]:
                        if pentry not in flist:
                            flist.append(pentry)
                    ptoc["files"] = flist
                    data = json.dumps(ptoc, indent=4).encode("utf-8")
                except Exception:
                    pass
            elif info.filename == "assets/dialogue_odr/toc.txt":
                try:
                    dtoc = json.loads(data.decode("utf-8"))
                    flist = dtoc.get("files", [])
                    for dentry in [
                        "dialogue/chromia_gs.png",
                        "dialogue/deadend_gs.png",
                    ]:
                        if dentry not in flist:
                            flist.append(dentry)
                    dtoc["files"] = flist
                    data = json.dumps(dtoc, indent=4).encode("utf-8")
                except Exception:
                    pass
            zout.writestr(info, data)
        # A pristine APK has no runtime hook entry. Replace it when rebuilding a
        # previous offline APK, or add it here when building from the original.
        if wanted_hook not in names:
            zout.writestr(wanted_hook, hook)

        # Ensure G1 Optimus Prime and G1 Starscream ODR packages are registered and available
        if char_bundle_data is not None:
            # Optimus Prime G1
            op_bundle_path = "assets/assetpack/optimusprime_gs_v_odr/optimusprime_gs_v.assetbundle"
            op_toc_path = "assets/optimusprime_gs_v_odr/toc.txt"
            if op_bundle_path not in names:
                zout.writestr(op_bundle_path, char_bundle_data)
            if op_toc_path not in names:
                op_toc_json = json.dumps({
                    "tags": [], "pack": "optimusprime_gs_v_odr", "scenes": {},
                    "bundles": {
                        "optimusprime_gs_v": {
                            "crc": 0, "compression": "LZ4", "typetreehash": None,
                            "file": "optimusprime_gs_v_odr/optimusprime_gs_v.assetbundle",
                            "ts": 637933503540000000, "deterministic": False, "manifest": "manifest_main",
                            "paths": {
                                "bundles/characters/merged/optimusprime_gs_v_lw": "Assets/Bundles/Characters/Merged/OptimusPrime_GS_V/OptimusPrime_GS_V_lw.prefab",
                                "bundles/characters/merged/optimusprime_gs_v": "Assets/Bundles/Characters/Merged/OptimusPrime_GS_V/OptimusPrime_GS_V.prefab"
                            },
                            "directory": "odr", "deps": ["character_fx", "moves", "character_audio"],
                            "contenthash": None, "size": len(char_bundle_data), "hash": 0, "parent": "", "mount": "None"
                        }
                    },
                    "files": [], "pad": {"deliverymode": 1, "assetpack": "default"}, "version": "9.2.0"
                }, indent=4)
                zout.writestr(op_toc_path, op_toc_json)

            # Starscream G1
            ss_bundle_path = "assets/assetpack/starscream_gs_odr/starscream_gs.assetbundle"
            ss_toc_path = "assets/starscream_gs_odr/toc.txt"
            if ss_bundle_path not in names:
                zout.writestr(ss_bundle_path, char_bundle_data)
            if ss_toc_path not in names:
                ss_toc_json = json.dumps({
                    "tags": [], "pack": "starscream_gs_odr", "scenes": {},
                    "bundles": {
                        "starscream_gs": {
                            "crc": 0, "compression": "LZ4", "typetreehash": None,
                            "file": "starscream_gs_odr/starscream_gs.assetbundle",
                            "ts": 637933503540000000, "deterministic": False, "manifest": "manifest_main",
                            "paths": {
                                "bundles/characters/merged/starscream_gs_lw": "Assets/Bundles/Characters/Merged/Starscream_GS/Starscream_GS_lw.prefab",
                                "bundles/characters/merged/starscream_gs": "Assets/Bundles/Characters/Merged/Starscream_GS/Starscream_GS.prefab"
                            },
                            "directory": "odr", "deps": ["character_fx", "moves", "character_audio"],
                            "contenthash": None, "size": len(char_bundle_data), "hash": 0, "parent": "", "mount": "None"
                        }
                    },
                    "files": [], "pad": {"deliverymode": 1, "assetpack": "default"}, "version": "9.2.0"
                }, indent=4)
                zout.writestr(ss_toc_path, ss_toc_json)

        # Inject Netflix Edition characters: Chromia and Dead End
        netflix_dir = Path("assets_netflix")
        if netflix_dir.is_dir():
            chromia_bundle = netflix_dir / "chromia_gs_kabam.assetbundle"
            if chromia_bundle.exists():
                cdata = chromia_bundle.read_bytes()
                zout.writestr("assets/assetpack/chromia_gs_kabam_odr/chromia_gs_kabam.assetbundle", cdata)
                chromia_mf = netflix_dir / "chromia_gs_kabam.assetbundle.manifest"
                if chromia_mf.exists():
                    zout.writestr("assets/assetpack/chromia_gs_kabam_odr/chromia_gs_kabam.assetbundle.manifest", chromia_mf.read_bytes())
                chromia_toc = json.dumps({
                    "tags": [], "pack": "chromia_gs_kabam_odr", "scenes": {},
                    "bundles": {
                        "chromia_gs_kabam": {
                            "crc": 0, "compression": "LZ4", "typetreehash": None,
                            "file": "chromia_gs_kabam_odr/chromia_gs_kabam.assetbundle",
                            "ts": 637933503540000000, "deterministic": False, "manifest": "manifest_main",
                            "paths": {
                                "bundles/characters/merged/chromia_gs_kabam_lw": "Assets/Bundles/Characters/Merged/Chromia_GS_Kabam/Chromia_GS_Kabam_lw.prefab",
                                "bundles/characters/merged/chromia_gs_kabam": "Assets/Bundles/Characters/Merged/Chromia_GS_Kabam/Chromia_GS_Kabam.prefab"
                            },
                            "directory": "odr", "deps": ["character_fx", "moves", "character_audio"],
                            "contenthash": None, "size": len(cdata), "hash": 0, "parent": "", "mount": "None"
                        }
                    },
                    "files": [], "pad": {"deliverymode": 1, "assetpack": "default"}, "version": "9.2.0"
                }, indent=4)
                zout.writestr("assets/chromia_gs_kabam_odr/toc.txt", chromia_toc)

            deadend_bundle = netflix_dir / "deadend_gs_deluxe2015.assetbundle"
            if deadend_bundle.exists():
                ddata = deadend_bundle.read_bytes()
                zout.writestr("assets/assetpack/deadend_gs_deluxe2015_odr/deadend_gs_deluxe2015.assetbundle", ddata)
                deadend_mf = netflix_dir / "deadend_gs_deluxe2015.assetbundle.manifest"
                if deadend_mf.exists():
                    zout.writestr("assets/assetpack/deadend_gs_deluxe2015_odr/deadend_gs_deluxe2015.assetbundle.manifest", deadend_mf.read_bytes())
                deadend_toc = json.dumps({
                    "tags": [], "pack": "deadend_gs_deluxe2015_odr", "scenes": {},
                    "bundles": {
                        "deadend_gs_deluxe2015": {
                            "crc": 0, "compression": "LZ4", "typetreehash": None,
                            "file": "deadend_gs_deluxe2015_odr/deadend_gs_deluxe2015.assetbundle",
                            "ts": 637933503540000000, "deterministic": False, "manifest": "manifest_main",
                            "paths": {
                                "bundles/characters/merged/deadend_gs_deluxe2015_lw": "Assets/Bundles/Characters/Merged/DeadEnd_GS_Deluxe2015/Deadend_GS_Deluxe2015_lw.prefab",
                                "bundles/characters/merged/deadend_gs_deluxe2015": "Assets/Bundles/Characters/Merged/DeadEnd_GS_Deluxe2015/Deadend_GS_Deluxe2015.prefab"
                            },
                            "directory": "odr", "deps": ["character_fx", "moves", "character_audio"],
                            "contenthash": None, "size": len(ddata), "hash": 0, "parent": "", "mount": "None"
                        }
                    },
                    "files": [], "pad": {"deliverymode": 1, "assetpack": "default"}, "version": "9.2.0"
                }, indent=4)
                zout.writestr("assets/deadend_gs_deluxe2015_odr/toc.txt", deadend_toc)

            # Portraits and Dialogue
            for fpath, ztarget in [
                ("portrait_chromia_gs_large.png", "assets/assetpack/portraits_odr/portraits/portrait_chromia_gs_large.png"),
                ("portrait_chromia_gs_small.jpg", "assets/assetpack/portraits_odr/portraits/portrait_chromia_gs_small.jpg"),
                ("portrait_deadend_gs_large.png", "assets/assetpack/portraits_odr/portraits/portrait_deadend_gs_large.png"),
                ("portrait_deadend_gs_small.jpg", "assets/assetpack/portraits_odr/portraits/portrait_deadend_gs_small.jpg"),
                ("chromia_gs.png", "assets/assetpack/dialogue_odr/dialogue/chromia_gs.png"),
                ("deadend_gs.png", "assets/assetpack/dialogue_odr/dialogue/deadend_gs.png"),
            ]:
                pfile = netflix_dir / fpath
                if pfile.exists():
                    zout.writestr(ztarget, pfile.read_bytes())

        if payload is not None:
            payload_info = zipfile.ZipInfo(PAYLOAD_ASSET, date_time=(1980, 1, 1, 0, 0, 0))
            payload_info.compress_type = zipfile.ZIP_STORED
            payload_info.external_attr = 0o644 << 16
            zout.writestr(payload_info, payload)
    return list(dict.fromkeys(changed_hosts))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument(
        "--server-host",
        type=validate_server_host,
        default=DEFAULT_SERVER_HOST,
        help=(
            "fake-server IPv4 address or DNS name reachable by the phone "
            f"(default: {DEFAULT_SERVER_HOST}, for adb reverse)"
        ),
    )
    parser.add_argument(
        "--scheme",
        choices=("https", "http"),
        default="https",
        help="fake-server URL scheme (default: https)",
    )
    parser.add_argument(
        "--server-port",
        type=validate_server_port,
        default=8443,
        help="fake-server TCP port in the range 1..65535 (default: 8443)",
    )
    parser.add_argument(
        "--abi",
        choices=sorted(ABIS),
        default=ARM64,
        help=f"native ABI to build for (default: {ARM64})",
    )
    parser.add_argument(
        "--keep-other-abi",
        action="store_true",
        help=(
            "keep the other ABI's native libraries. They are dropped by default "
            "because Android prefers arm64 whenever it is present, which would "
            "load the unpatched library instead of the patched one."
        ),
    )
    parser.add_argument(
        "--patched-il2cpp",
        type=Path,
        default=None,
        help=(
            "replace lib/<abi>/libil2cpp.so with this already-patched ELF. "
            "This avoids unpacking and repacking the whole source APK."
        ),
    )
    parser.add_argument(
        "--bundle-server",
        action="store_true",
        help=(
            "bake the plain-HTTP loopback server payload into the APK for either ABI "
            "(requires --scheme http --server-host 127.0.0.1)"
        ),
    )
    args = parser.parse_args()
    hosts = build(
        args.source,
        args.destination,
        args.server_host,
        args.abi,
        args.keep_other_abi,
        args.patched_il2cpp,
        scheme=args.scheme,
        server_port=args.server_port,
        bundle_server=args.bundle_server,
    )
    hook_path = ABIS[args.abi][0]
    print(f"wrote unsigned APK: {args.destination}")
    print(f"abi: {args.abi}" + ("" if args.keep_other_abi else " (other ABI's libraries dropped)"))
    print("redirected: " + ", ".join(hosts))
    print(f"fake server: {args.scheme}://{args.server_host}:{args.server_port}")
    if args.bundle_server:
        payload = export_payload.build_payload(args.server_port)
        route_count = len(export_payload.load_payload(payload).entries)
        print(
            f"bundled server payload: {PAYLOAD_ASSET} "
            f"({len(payload)} bytes, {route_count} routes, port {args.server_port})"
        )
    print(f"embedded runtime hook: {hook_path} ({hook_path.stat().st_size} bytes)")
    if args.patched_il2cpp is not None:
        print(f"embedded patched libil2cpp: {args.patched_il2cpp}")
    print("targetSdkVersion: preserved")


if __name__ == "__main__":
    main()
