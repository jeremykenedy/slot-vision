#!/usr/bin/env python3
"""Validate local documentation targets and XML assets."""
import re
from pathlib import Path
import xml.etree.ElementTree as ET
root = Path(__file__).resolve().parent.parent
for path in [root / 'AndroidManifest.xml', *root.glob('res/**/*.xml'), *root.glob('art/*.svg')]:
    ET.parse(path)
for path in [root / 'README.md', *root.glob('docs/**/*.md')]:
    text = path.read_text()
    assert '\u2014' not in text, str(path)
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if target.startswith(('https://', '#')):
            continue
        assert (path.parent / target.split('#')[0]).exists(), (path, target)
print('Documentation links and XML assets passed.')
