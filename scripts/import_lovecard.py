#!/usr/bin/env python3
"""Nhập nhạc từ các repo cũ (đã clone về máy) và các nguồn HTTP vào cấu trúc
<project>/<the-loai>/<ten-chuan>.mp3 theo lovecard/tracks.json.

    python3 scripts/import_lovecard.py --old /path/old_music [--old /path/old_mp3] [--fetch-http]

- File trong repo cũ được tìm theo tên gốc (không phân biệt hoa/thường, dấu NFC/NFD).
- File > max_file_mb sẽ được nén lại bằng ffmpeg (128 kbps) để jsDelivr phục vụ được.
- File còn lại trong repo cũ (web chưa dùng) cũng được nhập, phân loại theo tên.
"""
import argparse, json, os, re, shutil, subprocess, sys, unicodedata
from urllib.request import Request, urlopen
from slug import slug_filename

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
AUDIO_EXT = tuple(CFG["audio_ext"])
VI_CHARS = re.compile(r"[ăâđêôơưàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ]", re.I)
INSTR_WORDS = re.compile(r"piano|instrumental|giao hưởng|beat|lofi|không lời|remix", re.I)
BIRTHDAY_WORDS = re.compile(r"birthday|sinh nhật", re.I)


def norm(name):
    return unicodedata.normalize("NFC", name).strip().lower()


def category(name):
    if BIRTHDAY_WORDS.search(name):
        return "birthday"
    if INSTR_WORDS.search(name):
        return "instrumental"
    return "wedding-vn" if VI_CHARS.search(name) else "wedding-en"


def index_old(dirs):
    files = {}
    for d in dirs:
        for dp, dn, fn in os.walk(d):
            dn[:] = [x for x in dn if x != ".git"]
            for f in fn:
                if f.lower().endswith(AUDIO_EXT):
                    files.setdefault(norm(f), os.path.join(dp, f))
    return files


def shrink_if_needed(path):
    mb = os.path.getsize(path) / 1024 / 1024
    if mb <= CFG["max_file_mb"]:
        return mb
    tmp = path + ".tmp.mp3"
    print(f"   nén {os.path.basename(path)} ({mb:.1f} MB) -> 128 kbps")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-vn", "-b:a", "128k", tmp], check=True)
    os.replace(tmp, os.path.splitext(path)[0] + ".mp3")
    if not path.endswith(".mp3"):
        os.remove(path)
    return os.path.getsize(os.path.splitext(path)[0] + ".mp3") / 1024 / 1024


def fetch(url, dst):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=60) as r, open(dst, "wb") as f:
        shutil.copyfileobj(r, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", action="append", default=[], help="thư mục repo cũ đã clone")
    ap.add_argument("--fetch-http", action="store_true", help="tải cả nguồn HTTP ngoài GitHub")
    a = ap.parse_args()

    tracks = json.load(open(os.path.join(ROOT, "lovecard", "tracks.json"), encoding="utf-8"))
    old = index_old(a.old)
    used_old = set()
    ok, missing = [], []
    for t in tracks:
        dst = os.path.join(ROOT, t["new_path"])
        if os.path.exists(dst):
            ok.append(t); continue
        src = old.get(norm(t["original_name"]))
        if src:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            used_old.add(src)
            mb = shrink_if_needed(dst)
            print(f"OK  {t['new_path']}  ({mb:.1f} MB)  <- repo cũ")
            ok.append(t); continue
        if a.fetch_http:
            for u in t["sources"]:
                if "cdn.jsdelivr.net/gh/" in u:
                    continue
                try:
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    fetch(u, dst)
                    if os.path.getsize(dst) < 10_000:
                        raise RuntimeError("file quá nhỏ, có thể là trang lỗi")
                    mb = shrink_if_needed(dst)
                    print(f"OK  {t['new_path']}  ({mb:.1f} MB)  <- {u}")
                    ok.append(t); break
                except Exception as e:
                    if os.path.exists(dst):
                        os.remove(dst)
                    print(f"LỖI {u}: {e}")
            else:
                missing.append(t)
        else:
            missing.append(t)

    # Nhập nốt các file trong repo cũ mà web chưa dùng
    extra = 0
    for key, src in old.items():
        if src in used_old:
            continue
        fn = os.path.basename(src)
        dst = os.path.join(ROOT, "lovecard", category(fn), slug_filename(unicodedata.normalize("NFC", fn)))
        if os.path.exists(dst):
            continue
        shutil.copy2(src, dst)
        mb = shrink_if_needed(dst)
        print(f"OK  {os.path.relpath(dst, ROOT)}  ({mb:.1f} MB)  <- repo cũ (web chưa dùng)")
        extra += 1

    print(f"\n{len(ok)} bài web đang dùng đã có file, {extra} bài khác từ repo cũ, {len(missing)} bài thiếu:")
    for t in missing:
        print(f"  THIẾU {t['new_path']}  (dùng ở {t['page_count']} trang)  nguồn: {', '.join(t['sources'])}")
    with open(os.path.join(ROOT, "lovecard", "missing.json"), "w", encoding="utf-8") as f:
        json.dump(missing, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
