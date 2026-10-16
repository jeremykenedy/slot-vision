#!/usr/bin/env python3
"""Install, update, or remove Slot Vision from an Android TV over ADB."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


ROOT = Path(__file__).resolve().parent
APK = ROOT / "build" / "slot-vision.apk"
PACKAGE = "com.jeremykenedy.reelatrium"
REPOSITORY = "jeremykenedy/slot-vision"
APK_NAME = "slot-vision.apk"
CHECKSUM_NAME = APK_NAME + ".sha256"
RELEASE_API = "https://api.github.com/repos/{}/releases/latest".format(REPOSITORY)
ASSET_HOSTS = {"release-assets.githubusercontent.com", "objects.githubusercontent.com"}
MAX_RELEASE_BYTES = 1024 * 1024
MAX_APK_BYTES = 128 * 1024 * 1024
MAX_REDIRECTS = 3


def run(arguments):
    return subprocess.run(arguments, check=False, text=True, capture_output=True)


def devices():
    result = run(["adb", "devices"])
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "ADB could not list devices")
    return [line.split()[0] for line in result.stdout.splitlines()[1:]
            if len(line.split()) > 1 and line.split()[1] == "device"]


def choose_device(serial, available, allow_prompt=True):
    if serial:
        if serial not in available:
            raise RuntimeError("The requested ADB device is not connected or authorized")
        return serial
    if not available:
        raise RuntimeError("No authorized Android TV is connected. Connect it with ADB first")
    if len(available) == 1:
        return available[0]
    if not allow_prompt:
        raise RuntimeError("More than one Android device is connected. Pass --serial to choose one")
    print("  Connected Android devices:")
    for index, item in enumerate(available, start=1):
        print("    {}. {}".format(index, item))
    choice = input("  Choose a device number: ").strip()
    if not choice.isdigit() or not 1 <= int(choice) <= len(available):
        raise RuntimeError("Choose one of the listed device numbers")
    return available[int(choice) - 1]


def confirm(prompt, assume_yes):
    if assume_yes:
        return True
    return input("  {} [y/N] ".format(prompt)).strip().lower() in ("y", "yes")


def valid_https_url(value, hostname, path_prefix=""):
    if not isinstance(value, str):
        return False
    try:
        url = urlparse(value)
        return (url.scheme == "https" and url.hostname == hostname and not url.username
                and not url.password and url.port is None and url.path.startswith(path_prefix))
    except ValueError:
        return False


def release_asset_url(value):
    return valid_https_url(value, "github.com", "/{}/releases/download/".format(REPOSITORY))


def asset_redirect_url(value):
    if not isinstance(value, str):
        return False
    try:
        url = urlparse(value)
        return (url.scheme == "https" and url.hostname in ASSET_HOSTS and not url.username
                and not url.password and url.port is None)
    except ValueError:
        return False


class TrustedRedirectHandler(HTTPRedirectHandler):
    max_redirections = MAX_REDIRECTS
    max_repeats = MAX_REDIRECTS

    def __init__(self, allow_asset_redirects):
        super().__init__()
        self.allow_asset_redirects = allow_asset_redirects

    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        if not self.allow_asset_redirects or not asset_redirect_url(new_url):
            raise URLError("Refusing an unexpected release asset redirect")
        return super().redirect_request(request, file_pointer, code, message, headers, new_url)


def open_url(url, max_bytes, follow_release_redirects=False):
    redirect_handler = TrustedRedirectHandler(follow_release_redirects)
    opener = build_opener(redirect_handler)
    request = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "Slot-Vision-Installer"})
    with opener.open(request, timeout=30) as response:
        final_url = response.geturl()
        if follow_release_redirects and final_url != url and not asset_redirect_url(final_url):
            raise RuntimeError("The release download ended at an unexpected host")
        length = response.headers.get("Content-Length")
        if length:
            try:
                if int(length) > max_bytes:
                    raise RuntimeError("The release download is larger than the allowed size")
            except ValueError as error:
                raise RuntimeError("GitHub returned an invalid content length") from error
        body = response.read(max_bytes + 1)
    if len(body) > max_bytes:
        raise RuntimeError("The release download is larger than the allowed size")
    return body


def parse_checksum(text, filename):
    parts = (text or "").strip().split()
    if not parts or not re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
        return None
    if len(parts) > 2 or (len(parts) == 2 and parts[1].lstrip("*") != filename):
        return None
    return parts[0].lower()


def release_asset(release, filename):
    assets = release.get("assets", [])
    if not isinstance(assets, list):
        return None
    return next((item for item in assets if isinstance(item, dict) and item.get("name") == filename), None)


def download_latest_release():
    try:
        release = json.loads(open_url(RELEASE_API, MAX_RELEASE_BYTES).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("GitHub returned invalid release information") from error
    if not isinstance(release, dict):
        raise RuntimeError("GitHub returned invalid release information")
    apk_asset = release_asset(release, APK_NAME)
    checksum_asset = release_asset(release, CHECKSUM_NAME)
    if apk_asset is None or checksum_asset is None:
        raise RuntimeError("The latest release must include the APK and its SHA-256 file")
    apk_url = apk_asset.get("browser_download_url", "")
    checksum_url = checksum_asset.get("browser_download_url", "")
    if not release_asset_url(apk_url) or not release_asset_url(checksum_url):
        raise RuntimeError("The release contains an unexpected download URL")
    try:
        checksum_text = open_url(checksum_url, 4096, follow_release_redirects=True).decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError("The release checksum is not valid UTF-8") from error
    expected = parse_checksum(checksum_text, APK_NAME)
    if expected is None:
        raise RuntimeError("The release checksum is missing or does not name the APK")
    apk_bytes = open_url(apk_url, MAX_APK_BYTES, follow_release_redirects=True)
    actual = hashlib.sha256(apk_bytes).hexdigest()
    if actual != expected:
        raise RuntimeError("The APK checksum does not match the published release checksum")
    directory = Path(tempfile.mkdtemp(prefix="slot-vision-"))
    try:
        os.chmod(directory, 0o700)
        apk_path = directory / APK_NAME
        apk_path.write_bytes(apk_bytes)
        os.chmod(apk_path, 0o600)
    except OSError:
        shutil.rmtree(directory, ignore_errors=True)
        raise
    return apk_path, directory, release.get("tag_name", "latest")


def banner():
    print()
    print("  +--------------------------------------------------+")
    print("  |                 SLOT VISION                     |")
    print("  |               SCREENSAVER INSTALLER             |")
    print("  +--------------------------------------------------+")
    print()


def color(text, code):
    if sys.stdout.isatty() and not os.getenv("NO_COLOR"):
        return "\033[{}m{}\033[0m".format(code, text)
    return text


def step(number, total, label):
    print("  {} {}".format(color("[{}/{}]".format(number, total), "1;36"), label))


def main():
    parser = argparse.ArgumentParser(description="Install or remove Slot Vision on an Android TV")
    parser.add_argument("--serial", help="ADB serial or TV_IP:5555")
    parser.add_argument("--apk", type=Path, help="Install a local APK instead of the latest verified release")
    parser.add_argument("--uninstall", action="store_true", help="Remove Slot Vision")
    parser.add_argument("--yes", action="store_true", help="Confirm installation or update")
    parser.add_argument("--force", action="store_true", help="Allow non-interactive removal with --yes")
    args = parser.parse_args()
    if args.uninstall and args.apk:
        parser.error("--apk cannot be combined with --uninstall")
    if args.uninstall and args.yes and not args.force:
        parser.error("--yes does not confirm removal; use --force with --uninstall")
    if args.uninstall and not sys.stdin.isatty() and not (args.yes and args.force):
        parser.error("Non-interactive removal requires --uninstall --yes --force")
    if args.uninstall and args.yes and args.force and not sys.stdin.isatty():
        approved = True
    elif args.uninstall:
        approved = confirm("Remove Slot Vision and its local settings?", False)
    else:
        approved = confirm("Install or update Slot Vision from its latest release?", args.yes)
    if not approved:
        print("\n  Cancelled. No device changes were made.")
        return 0
    local_apk = None
    if not args.uninstall and args.apk:
        local_apk = args.apk.expanduser().resolve()
        if not local_apk.is_file():
            raise RuntimeError("Local APK not found: {}".format(local_apk))
    banner()
    total_steps = 2 if args.uninstall or args.apk else 3
    step(1, total_steps, "Finding your TV")
    serial = choose_device(args.serial, devices(), sys.stdin.isatty())
    print("       Connected to {}".format(serial))
    command = ["adb", "-s", serial]
    if args.uninstall:
        operation = command + ["uninstall", PACKAGE]
        release_directory = None
    else:
        if local_apk:
            apk_path = local_apk
            release_directory = None
            print("\n  Using local APK: {}".format(apk_path))
        else:
            step(2, total_steps, "Downloading and verifying the latest release")
            apk_path, release_directory, tag = download_latest_release()
            print("       Release {} verified against its published SHA-256".format(tag))
        operation = command + ["install", "-r", str(apk_path)]
    if args.uninstall:
        print("\n  Removing Slot Vision and its settings")
    else:
        print("\n  Installing or updating Slot Vision")
    step(total_steps, total_steps, "Applying the change")
    try:
        result = run(operation)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "ADB command failed")
        print("       {}".format(color("Complete", "1;32")))
        if result.stdout.strip():
            print("       {}".format(result.stdout.strip()))
        print("\n  The app does not change the TV's screensaver selection or system timers.")
    finally:
        if not args.uninstall and not args.apk and release_directory:
            shutil.rmtree(release_directory, ignore_errors=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError) as error:
        print("\n  Failed: {}\n".format(error), file=sys.stderr)
        raise SystemExit(1)
