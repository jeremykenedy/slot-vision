#!/usr/bin/env python3
"""Verify the app manifest and source remain free of runtime network/reporting code."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ANDROID = "{http://schemas.android.com/apk/res/android}"
FORBIDDEN_SOURCE = re.compile(
    r"\b(Analytics|Crashlytics|FirebaseAnalytics|HttpURLConnection|OkHttpClient|Retrofit|WebView)\b"
)


def check_privacy(root=ROOT):
    errors = []
    manifest = ET.parse(root / "AndroidManifest.xml").getroot()
    for permission in manifest.findall("uses-permission"):
        name = permission.get(ANDROID + "name", "")
        if name in ("android.permission.INTERNET", "android.permission.ACCESS_NETWORK_STATE"):
            errors.append("Manifest requests runtime network permission: {}".format(name))
    for source in sorted((root / "src").rglob("*.java")):
        text = source.read_text(encoding="utf-8")
        if FORBIDDEN_SOURCE.search(text):
            errors.append("Network or reporting client found in {}".format(source.relative_to(root)))
    return errors


if __name__ == "__main__":
    problems = check_privacy()
    if problems:
        for problem in problems:
            print(problem)
        raise SystemExit(1)
    print("No runtime network permission or reporting client was found.")
