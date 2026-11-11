#!/usr/bin/env python3
"""Checks the documentation of this repository, with the standard library only.

- Every relative link and image in the Markdown files points at a file that exists,
  and every #anchor at a heading of the page it links to.
- Every PNG holds only the image itself (IHDR, IDAT, IEND): no text chunks, so no
  capture time and no program name travel with a screenshot.

Run it from the root of the repository: python3 .github/scripts/check-docs.py
"""
import re
import struct
import subprocess
import sys
from pathlib import Path

LINK = re.compile(r'!?\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
HTML_LINK = re.compile(r'<(?:a|img)\b[^>]*?\b(?:href|src)="([^"]+)"')
HEADING = re.compile(r'^#{1,6}\s+(.*)$', re.M)
FENCE = re.compile(r'```.*?```', re.S)


def tracked(pattern):
    out = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard', pattern],
                         capture_output=True, text=True, check=True).stdout
    return [Path(line) for line in out.splitlines() if Path(line).exists()]


def slug(heading):
    """The anchor GitHub gives a heading: lower case, punctuation dropped, spaces to hyphens."""
    text = re.sub(r'[`*_]', '', heading.strip().lower())
    return re.sub(r'[^\w\- ]', '', text).replace(' ', '-')


def check_links():
    pages = tracked('*.md')
    anchors = {p: {slug(h) for h in HEADING.findall(FENCE.sub('', p.read_text(encoding='utf-8')))} for p in pages}
    problems, count = [], 0
    for page in pages:
        text = FENCE.sub('', page.read_text(encoding='utf-8'))
        for target in LINK.findall(text) + HTML_LINK.findall(text):
            if re.match(r'[a-z][a-z0-9+.-]*:', target):
                continue  # http, https, mailto: not checked here
            count += 1
            path, _, anchor = target.partition('#')
            dest = (page.parent / path) if path else page
            if not dest.exists():
                problems.append(f'{page}: {target} does not exist')
            elif anchor and dest.suffix == '.md':
                known = anchors.get(Path(*dest.resolve().relative_to(Path.cwd().resolve()).parts))
                if known is not None and anchor not in known:
                    problems.append(f'{page}: {target} has no such heading')
    print(f'{count} relative links and images in {len(pages)} pages')
    return problems


def check_images():
    problems = []
    images = tracked('*.png')
    for image in images:
        data = image.read_bytes()
        if data[:8] != b'\x89PNG\r\n\x1a\n':
            problems.append(f'{image}: not a PNG file')
            continue
        pos, chunks = 8, set()
        while pos + 8 <= len(data):
            length, kind = struct.unpack('>I4s', data[pos:pos + 8])
            chunks.add(kind.decode('latin-1'))
            pos += 12 + length
        extra = chunks - {'IHDR', 'IDAT', 'IEND', 'PLTE', 'tRNS'}
        if extra or pos != len(data):
            problems.append(f'{image}: carries more than the image ({", ".join(sorted(extra)) or "trailing data"})')
    print(f'{len(images)} PNG images')
    return problems


if __name__ == '__main__':
    found = check_links() + check_images()
    for line in found:
        print(f'::error::{line}')
    sys.exit(1 if found else 0)
