#!/usr/bin/env python3
"""Sinh index.json và URLS.md: mọi file audio + URL jsDelivr tương ứng."""
import json, os, re, time
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
SKIP = {".git", "scripts", ".venv", "__pycache__"}
SAFE = re.compile(r"^[a-z0-9._-]+$")


def cdn_base():
    return CFG["cdn_base"].format(user=CFG["github_user"], repo=CFG["github_repo"],
                                  branch=CFG["branch"])


def main():
    base = cdn_base()
    items, warnings = [], []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP and not d.startswith("."))
        for fn in sorted(filenames):
            if os.path.splitext(fn)[1].lower() not in CFG["audio_ext"]:
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            parts = rel.split("/")
            size_mb = os.path.getsize(full) / 1024 / 1024
            if not SAFE.match(fn):
                warnings.append(f"Tên file chưa chuẩn (chạy normalize.py): {rel}")
            if size_mb > CFG["max_file_mb"]:
                warnings.append(f"File {rel} = {size_mb:.1f} MB > {CFG['max_file_mb']} MB, jsDelivr sẽ không phục vụ")
            items.append({
                "project": parts[0] if len(parts) > 2 else "",
                "category": parts[1] if len(parts) > 2 else (parts[0] if len(parts) > 1 else ""),
                "file": fn,
                "path": rel,
                "size_mb": round(size_mb, 2),
                "url": base + quote(rel),
            })
    index = {"generated": time.strftime("%Y-%m-%d %H:%M:%S"), "cdn_base": base,
             "count": len(items), "files": items}
    with open(os.path.join(ROOT, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)

    lines = ["# Danh sách URL nhạc nền (sinh tự động bởi scripts/build_index.py)", "",
             f"CDN base: `{base}`", ""]
    cur = None
    for it in items:
        key = (it["project"], it["category"])
        if key != cur:
            cur = key
            lines += ["", f"## {it['project']} / {it['category']}", "",
                      "| File | MB | URL |", "|---|---:|---|"]
        lines.append(f"| {it['file']} | {it['size_mb']} | {it['url']} |")
    if warnings:
        lines += ["", "## Cảnh báo", ""] + [f"- {w}" for w in warnings]
    with open(os.path.join(ROOT, "URLS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{len(items)} file -> index.json, URLS.md")
    for w in warnings:
        print("CẢNH BÁO:", w)


if __name__ == "__main__":
    main()
