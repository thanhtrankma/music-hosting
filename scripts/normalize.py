#!/usr/bin/env python3
"""Đổi tên mọi file audio trong repo về dạng slug (không dấu, không khoảng trắng).

    python3 scripts/normalize.py          # đổi tên thật
    python3 scripts/normalize.py --dry    # chỉ in ra, không đổi
"""
import json, os, sys
from slug import slug_filename

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
SKIP = {".git", "scripts", ".venv", "__pycache__"}


def main():
    dry = "--dry" in sys.argv
    changed = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP and not d.startswith(".")]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() not in CFG["audio_ext"]:
                continue
            new = slug_filename(fn)
            if new == fn:
                continue
            src, dst = os.path.join(dirpath, fn), os.path.join(dirpath, new)
            if os.path.exists(dst):
                print(f"BỎ QUA (trùng tên): {src} -> {new}")
                continue
            print(f"{'[dry] ' if dry else ''}{os.path.relpath(src, ROOT)} -> {new}")
            if not dry:
                os.rename(src, dst)
            changed += 1
    print(f"{changed} file được đổi tên" + (" (chế độ dry-run)" if dry else ""))


if __name__ == "__main__":
    main()
