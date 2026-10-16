import hashlib
import io
import json
import runpy
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError
from urllib.request import Request

import install


class FakeResponse(io.BytesIO):
    def __init__(self, body, url, content_length=None):
        super().__init__(body)
        self.url = url
        self.headers = {"Content-Length": str(content_length)} if content_length is not None else {}

    def geturl(self):
        return self.url

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


class FakeOpener:
    def __init__(self, response):
        self.response = response
        self.request = None
        self.timeout = None

    def open(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return self.response


def release_data(apk_bytes=b"signed apk", apk_url=None, checksum_url=None, tag="v1.0.0"):
    apk_url = apk_url or "https://github.com/{}/releases/download/v1.0.0/{}".format(install.REPOSITORY, install.APK_NAME)
    checksum_url = checksum_url or "https://github.com/{}/releases/download/v1.0.0/{}".format(install.REPOSITORY, install.CHECKSUM_NAME)
    digest = hashlib.sha256(apk_bytes).hexdigest()
    release = {
        "tag_name": tag,
        "assets": [
            {"name": install.APK_NAME, "browser_download_url": apk_url},
            {"name": install.CHECKSUM_NAME, "browser_download_url": checksum_url},
        ],
    }
    return release, apk_bytes, "{}  {}\n".format(digest, install.APK_NAME)


class InstallerTest(unittest.TestCase):
    def test_run_uses_captured_nonraising_subprocess(self):
        result = object()
        with patch.object(install.subprocess, "run", return_value=result) as mocked_run:
            self.assertIs(result, install.run(["adb", "devices"]))
        mocked_run.assert_called_once_with(["adb", "devices"], check=False, text=True, capture_output=True)

    def test_devices_returns_only_authorized_serials(self):
        result = type("Result", (), {"returncode": 0, "stdout": "List\nTV1 device\nTV2 unauthorized\noffline offline\n", "stderr": ""})()
        with patch.object(install, "run", return_value=result):
            self.assertEqual(["TV1"], install.devices())

    def test_devices_reports_adb_failure(self):
        result = type("Result", (), {"returncode": 1, "stdout": "", "stderr": "adb unavailable"})()
        with patch.object(install, "run", return_value=result):
            with self.assertRaisesRegex(RuntimeError, "adb unavailable"):
                install.devices()

    def test_choose_device_validates_and_selects(self):
        self.assertEqual("TV1", install.choose_device("TV1", ["TV1"]))
        self.assertEqual("TV1", install.choose_device(None, ["TV1"]))
        with self.assertRaisesRegex(RuntimeError, "not connected"):
            install.choose_device("TV2", ["TV1"])
        with patch("builtins.input", return_value="2"):
            self.assertEqual("TV2", install.choose_device(None, ["TV1", "TV2"]))
        with self.assertRaisesRegex(RuntimeError, "Pass --serial"):
            install.choose_device(None, ["TV1", "TV2"], allow_prompt=False)
        with self.assertRaisesRegex(RuntimeError, "No authorized"):
            install.choose_device(None, [])
        for choice in ("", "0", "3", "x"):
            with patch("builtins.input", return_value=choice):
                with self.assertRaisesRegex(RuntimeError, "listed device numbers"):
                    install.choose_device(None, ["TV1", "TV2"])

    def test_confirm_handles_flag_and_prompt(self):
        self.assertTrue(install.confirm("continue?", True))
        with patch("builtins.input", return_value="yes"):
            self.assertTrue(install.confirm("continue?", False))
        with patch("builtins.input", return_value="n"):
            self.assertFalse(install.confirm("continue?", False))

    def test_url_validation_accepts_only_release_asset_and_redirect_hosts(self):
        apk_url = "https://github.com/{}/releases/download/v1/{}".format(install.REPOSITORY, install.APK_NAME)
        self.assertTrue(install.release_asset_url(apk_url))
        for value in (
            None,
            "http://github.com/{}/releases/download/v1/app.apk".format(install.REPOSITORY),
            "https://github.com/other/repo/releases/download/v1/app.apk",
            "https://user@github.com/{}/releases/download/v1/app.apk".format(install.REPOSITORY),
            "https://github.com:443/{}/releases/download/v1/app.apk".format(install.REPOSITORY),
            "https://github.com.evil.test/{}/releases/download/v1/app.apk".format(install.REPOSITORY),
            "https://github.com/{}/blob/main/app.apk".format(install.REPOSITORY),
            "https://github.com:{}/x".format("bad"),
        ):
            self.assertFalse(install.release_asset_url(value))
        self.assertTrue(install.asset_redirect_url("https://release-assets.githubusercontent.com/file"))
        self.assertTrue(install.asset_redirect_url("https://objects.githubusercontent.com/file"))
        for value in (None, "https://[bad", "https://objects.githubusercontent.com:bad/file",
                      "http://release-assets.githubusercontent.com/file", "https://github.com/file",
                      "https://user@objects.githubusercontent.com/file", "https://objects.githubusercontent.com:44/file"):
            self.assertFalse(install.asset_redirect_url(value))

    def test_redirect_handler_rejects_untrusted_hosts(self):
        request = Request("https://github.com/{}/releases/download/v1/app.apk".format(install.REPOSITORY))
        headers = {}
        handler = install.TrustedRedirectHandler(True)
        accepted = handler.redirect_request(request, io.BytesIO(), 302, "Found", headers,
                                            "https://release-assets.githubusercontent.com/app.apk")
        self.assertEqual("release-assets.githubusercontent.com", accepted.host)
        with self.assertRaises(URLError):
            handler.redirect_request(request, io.BytesIO(), 302, "Found", headers, "https://evil.test/app.apk")
        with self.assertRaises(URLError):
            install.TrustedRedirectHandler(False).redirect_request(
                request, io.BytesIO(), 302, "Found", headers, "https://release-assets.githubusercontent.com/app.apk"
            )

    def test_open_url_sets_headers_and_limits_response_size(self):
        url = install.RELEASE_API
        response = FakeResponse(b"release", url, content_length=7)
        opener = FakeOpener(response)
        with patch.object(install, "build_opener", return_value=opener) as build:
            self.assertEqual(b"release", install.open_url(url, 7))
        self.assertEqual(30, opener.timeout)
        self.assertIsInstance(opener.request, Request)
        self.assertEqual("application/vnd.github+json", opener.request.get_header("Accept"))
        build.assert_called_once()
        with patch.object(install, "build_opener", return_value=FakeOpener(FakeResponse(b"too long", url))):
            with self.assertRaisesRegex(RuntimeError, "allowed size"):
                install.open_url(url, 2)
        with patch.object(install, "build_opener", return_value=FakeOpener(FakeResponse(b"x", url, content_length=9))):
            with self.assertRaisesRegex(RuntimeError, "allowed size"):
                install.open_url(url, 2)
        with patch.object(install, "build_opener", return_value=FakeOpener(FakeResponse(b"x", url, content_length="bad"))):
            with self.assertRaisesRegex(RuntimeError, "invalid content length"):
                install.open_url(url, 2)

    def test_open_url_checks_final_asset_host(self):
        apk_url = "https://github.com/{}/releases/download/v1/app.apk".format(install.REPOSITORY)
        allowed = FakeResponse(b"apk", "https://release-assets.githubusercontent.com/app.apk")
        with patch.object(install, "build_opener", return_value=FakeOpener(allowed)):
            self.assertEqual(b"apk", install.open_url(apk_url, 10, follow_release_redirects=True))
        rejected = FakeResponse(b"apk", "https://evil.test/app.apk")
        with patch.object(install, "build_opener", return_value=FakeOpener(rejected)):
            with self.assertRaisesRegex(RuntimeError, "unexpected host"):
                install.open_url(apk_url, 10, follow_release_redirects=True)

    def test_parse_checksum_requires_the_expected_file_name(self):
        digest = "A" * 64
        self.assertEqual(digest.lower(), install.parse_checksum(digest, install.APK_NAME))
        self.assertEqual(digest.lower(), install.parse_checksum("{} *{}\n".format(digest, install.APK_NAME), install.APK_NAME))
        for content in (None, "", "bad", digest + " other.apk", digest + " one two"):
            self.assertIsNone(install.parse_checksum(content, install.APK_NAME))

    def test_release_asset_ignores_invalid_entries(self):
        release = {"assets": [None, "bad", {"name": "other.apk"}]}
        self.assertIsNone(install.release_asset(release, install.APK_NAME))
        self.assertIsNone(install.release_asset({"assets": "bad"}, install.APK_NAME))
        self.assertIsNone(install.release_asset({}, install.APK_NAME))

    def test_download_latest_release_verifies_checksum_and_writes_private_temp_file(self):
        release, apk_bytes, checksum = release_data()
        payloads = {
            install.RELEASE_API: json.dumps(release).encode(),
            release["assets"][1]["browser_download_url"]: checksum.encode(),
            release["assets"][0]["browser_download_url"]: apk_bytes,
        }
        calls = []

        def fetch(url, max_bytes, follow_release_redirects=False):
            calls.append((url, max_bytes, follow_release_redirects))
            return payloads[url]

        with patch.object(install, "open_url", side_effect=fetch):
            apk_path, directory, tag = install.download_latest_release()
        try:
            self.assertEqual("v1.0.0", tag)
            self.assertEqual(apk_bytes, apk_path.read_bytes())
            self.assertEqual(0o700, directory.stat().st_mode & 0o777)
            self.assertEqual(0o600, apk_path.stat().st_mode & 0o777)
            self.assertEqual(3, len(calls))
            self.assertEqual(install.MAX_APK_BYTES, calls[-1][1])
            self.assertTrue(calls[-1][2])
        finally:
            shutil.rmtree(directory)

    def test_download_latest_release_rejects_invalid_metadata_assets_urls_and_checksum(self):
        with patch.object(install, "open_url", return_value=b"not json"):
            with self.assertRaisesRegex(RuntimeError, "invalid release information"):
                install.download_latest_release()
        with patch.object(install, "open_url", return_value=b"\xff"):
            with self.assertRaisesRegex(RuntimeError, "invalid release information"):
                install.download_latest_release()
        with patch.object(install, "open_url", return_value=json.dumps([]).encode()):
            with self.assertRaisesRegex(RuntimeError, "invalid release information"):
                install.download_latest_release()
        for release in ({}, {"assets": "bad"}, {"assets": [{"name": install.APK_NAME}]}):
            with patch.object(install, "open_url", return_value=json.dumps(release).encode()):
                with self.assertRaisesRegex(RuntimeError, "must include"):
                    install.download_latest_release()
        release, _apk, _sum = release_data(apk_url="https://evil.test/app.apk")
        with patch.object(install, "open_url", return_value=json.dumps(release).encode()):
            with self.assertRaisesRegex(RuntimeError, "unexpected download URL"):
                install.download_latest_release()
        release, _apk, _sum = release_data()
        urls = [release["assets"][1]["browser_download_url"], release["assets"][0]["browser_download_url"]]
        for checksum in (b"no checksum", b"\xff"):
            with patch.object(install, "open_url", side_effect=[json.dumps(release).encode(), checksum]):
                expected = "not valid UTF-8" if checksum == b"\xff" else "missing or does not name"
                with self.assertRaisesRegex(RuntimeError, expected):
                    install.download_latest_release()
        with patch.object(install, "open_url", side_effect=[json.dumps(release).encode(), b"0" * 64, b"wrong apk"]):
            with self.assertRaisesRegex(RuntimeError, "does not match"):
                install.download_latest_release()
        self.assertEqual(2, len(urls))

    def test_download_latest_release_cleans_up_if_temp_file_creation_fails(self):
        release, apk_bytes, checksum = release_data()
        payloads = [json.dumps(release).encode(), checksum.encode(), apk_bytes]
        with patch.object(install, "open_url", side_effect=payloads), \
                patch.object(Path, "write_bytes", side_effect=OSError("disk full")), \
                patch.object(install.shutil, "rmtree") as remove_temp:
            with self.assertRaisesRegex(OSError, "disk full"):
                install.download_latest_release()
        remove_temp.assert_called_once()

    def test_install_requires_local_apk_and_confirmation(self):
        missing = Path("missing.apk")
        with patch.object(sys, "argv", ["install.py", "--apk", str(missing), "--yes"]), \
                patch.object(Path, "is_file", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "Local APK not found"):
                install.main()
        output = io.StringIO()
        with patch.object(sys, "argv", ["install.py"]), patch.object(sys.stdin, "isatty", return_value=True), \
                patch("builtins.input", return_value="no"), redirect_stdout(output):
            self.assertEqual(0, install.main())
        self.assertIn("No device changes", output.getvalue())

    def test_install_runs_a_local_apk_on_the_selected_device(self):
        result = type("Result", (), {"returncode": 0, "stdout": "Success", "stderr": ""})()
        output = io.StringIO()
        with patch.object(sys, "argv", ["install.py", "--yes", "--serial", "TV1", "--apk", "local.apk"]), \
                patch.object(Path, "is_file", return_value=True), patch.object(install, "devices", return_value=["TV1"]), \
                patch.object(install, "run", return_value=result) as mocked_run, redirect_stdout(output):
            self.assertEqual(0, install.main())
        self.assertEqual(["adb", "-s", "TV1", "install", "-r", str(Path("local.apk").resolve())], mocked_run.call_args.args[0])
        self.assertIn("does not change the TV's screensaver", output.getvalue())
        self.assertIn("[2/2] Applying the change", output.getvalue())

    def test_install_from_release_cleans_temporary_apk_even_when_adb_fails(self):
        for returncode in (0, 1):
            with tempfile.TemporaryDirectory() as parent:
                directory = Path(parent) / "release"
                directory.mkdir()
                apk_path = directory / install.APK_NAME
                apk_path.write_bytes(b"verified")
                result = type("Result", (), {"returncode": returncode, "stdout": "Success", "stderr": "install failed" if returncode else ""})()
                output = io.StringIO()
                with patch.object(sys, "argv", ["install.py", "--yes", "--serial", "TV1"]), \
                        patch.object(install, "devices", return_value=["TV1"]), \
                        patch.object(install, "download_latest_release", return_value=(apk_path, directory, "v1.0.0")), \
                        patch.object(install, "run", return_value=result), redirect_stdout(output):
                    if returncode:
                        with self.assertRaisesRegex(RuntimeError, "install failed"):
                            install.main()
                    else:
                        self.assertEqual(0, install.main())
                self.assertFalse(directory.exists())
                self.assertIn("v1.0.0 verified", output.getvalue())

    def test_install_needs_a_serial_when_multiple_devices_are_connected(self):
        with patch.object(sys, "argv", ["install.py", "--yes"]), patch.object(install, "devices", return_value=["TV1", "TV2"]), \
                patch.object(install, "download_latest_release") as download:
            with self.assertRaisesRegex(RuntimeError, "Pass --serial"):
                install.main()
        download.assert_not_called()

    def test_uninstall_requires_explicit_confirmation_for_noninteractive_use(self):
        for arguments in (("--uninstall", "--yes"), ("--uninstall",)):
            with patch.object(sys, "argv", ["install.py", *arguments]), patch.object(sys.stdin, "isatty", return_value=False):
                with self.assertRaises(SystemExit):
                    install.main()
        with patch.object(sys, "argv", ["install.py", "--uninstall", "--apk", "x.apk"]):
            with self.assertRaises(SystemExit):
                install.main()

    def test_uninstall_confirmation_and_result(self):
        with patch.object(sys, "argv", ["install.py", "--uninstall"]), patch.object(sys.stdin, "isatty", return_value=True), \
                patch("builtins.input", return_value="no"), \
                redirect_stdout(io.StringIO()):
            self.assertEqual(0, install.main())
        result = type("Result", (), {"returncode": 0, "stdout": "Success", "stderr": ""})()
        with patch.object(sys, "argv", ["install.py", "--uninstall", "--yes", "--force"]), \
                patch.object(sys.stdin, "isatty", return_value=False), patch.object(install, "devices", return_value=["TV1"]), \
                patch.object(install, "run", return_value=result) as mocked_run, redirect_stdout(io.StringIO()):
            self.assertEqual(0, install.main())
        self.assertEqual(["adb", "-s", "TV1", "uninstall", install.PACKAGE], mocked_run.call_args.args[0])

    def test_missing_device_and_adb_operation_failure_are_reported(self):
        with patch.object(sys, "argv", ["install.py", "--yes"]), patch.object(install, "devices", return_value=[]):
            with self.assertRaisesRegex(RuntimeError, "No authorized"):
                install.main()
        failed = type("Result", (), {"returncode": 1, "stdout": "", "stderr": "install failed"})()
        with patch.object(sys, "argv", ["install.py", "--yes", "--apk", "local.apk"]), \
                patch.object(Path, "is_file", return_value=True), patch.object(install, "devices", return_value=["TV1"]), \
                patch.object(install, "run", return_value=failed), redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, "install failed"):
                install.main()
        success_without_output = type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        with patch.object(sys, "argv", ["install.py", "--yes", "--apk", "local.apk"]), \
                patch.object(Path, "is_file", return_value=True), patch.object(install, "devices", return_value=["TV1"]), \
                patch.object(install, "run", return_value=success_without_output), redirect_stdout(io.StringIO()):
            self.assertEqual(0, install.main())

    def test_interactive_force_removal_still_asks(self):
        result = type("Result", (), {"returncode": 0, "stdout": "Success", "stderr": ""})()
        with patch.object(sys, "argv", ["install.py", "--uninstall", "--yes", "--force"]), \
                patch.object(sys.stdin, "isatty", return_value=True), patch("builtins.input", return_value="yes"), \
                patch.object(install, "devices", return_value=["TV1"]), patch.object(install, "run", return_value=result), \
                redirect_stdout(io.StringIO()):
            self.assertEqual(0, install.main())

    def test_color_is_used_only_for_interactive_output(self):
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(install.os.environ, {}, clear=True):
            self.assertTrue(install.color("title", "1;36").startswith("\033["))
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(install.os.environ, {"NO_COLOR": "1"}):
            self.assertEqual("title", install.color("title", "1;36"))
        with patch.object(sys.stdout, "isatty", return_value=False):
            self.assertEqual("title", install.color("title", "1;36"))

    def test_command_entrypoint_success_and_failure(self):
        success = type("Result", (), {"returncode": 0, "stdout": "Success", "stderr": ""})()
        device_list = type("Result", (), {"returncode": 0, "stdout": "List\nTV1 device\n", "stderr": ""})()
        with patch.object(sys, "argv", ["install.py", "--yes", "--serial", "TV1", "--apk", "local.apk"]), \
                patch.object(Path, "is_file", return_value=True), patch.object(install.subprocess, "run", side_effect=[device_list, success]), \
                redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                runpy.run_path(str(install.ROOT / "install.py"), run_name="__main__")
        self.assertEqual(0, result.exception.code)
        failed_devices = type("Result", (), {"returncode": 1, "stdout": "", "stderr": "adb unavailable"})()
        errors = io.StringIO()
        with patch.object(sys, "argv", ["install.py", "--yes"]), patch.object(install.subprocess, "run", return_value=failed_devices), \
                redirect_stderr(errors):
            with self.assertRaises(SystemExit) as result:
                runpy.run_path(str(install.ROOT / "install.py"), run_name="__main__")
        self.assertEqual(1, result.exception.code)
        self.assertIn("adb unavailable", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
