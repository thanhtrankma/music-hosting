#!/usr/bin/env python3
"""Quét HTML gốc của web LoveCard đã clone (../lovecard/raw) để liệt kê các file
nhạc nền đang dùng, đề xuất thư mục + tên file chuẩn trong repo này, và sinh
lovecard/TRACKS.md + lovecard/tracks.json (kèm URL cũ -> URL mới để sửa web).

    python3 scripts/lovecard_migration.py [--raw ../lovecard/raw]
"""
import glob, json, os, re, sys, unicodedata
from collections import defaultdict
from urllib.parse import unquote, quote
from slug import slug_filename

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
RAW = sys.argv[sys.argv.index("--raw") + 1] if "--raw" in sys.argv else \
    os.path.join(os.path.dirname(ROOT), "lovecard", "raw")

AUDIO_RE = re.compile(r"""(?:src|href)=(["'])(https?://(?:(?!\1)[^<>])+?\.(?:mp3|m4a|wav|ogg))\s*\1""", re.I)
VI_CHARS = re.compile(r"[ăâđêôơưàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ]", re.I)
INSTR_WORDS = re.compile(r"piano|instrumental|giao hưởng|beat|lofi|không lời|remix", re.I)
BIRTHDAY_WORDS = re.compile(r"birthday|sinh nhật", re.I)


def category(name):
    if BIRTHDAY_WORDS.search(name):
        return "birthday"
    if INSTR_WORDS.search(name):
        return "instrumental"
    return "wedding-vn" if VI_CHARS.search(name) else "wedding-en"


def main():
    uses = defaultdict(set)        # url gốc đã làm sạch -> set(trang)
    raw_forms = defaultdict(set)   # url sạch -> các dạng thô xuất hiện trong HTML
    for f in glob.glob(os.path.join(RAW, "*", "*.html")):
        page = os.path.basename(f)[:-5]
        for _q, u in set(AUDIO_RE.findall(open(f, encoding="utf-8").read())):
            clean = re.sub(r"\s+", " ", u).strip()
            clean = re.sub(r"/\s+", "/", clean)        # "host/\n\nfile" -> "host/file"
            clean = clean.replace(" /", "/")
            uses[clean].add(page)
            raw_forms[clean].add(u)

    base = CFG["cdn_base"].format(user=CFG["github_user"], repo=CFG["github_repo"],
                                  branch=CFG["branch"])
    prev_file = os.path.join(ROOT, "lovecard", "tracks.json")
    prev_sources = {}
    if os.path.exists(prev_file):
        for t in json.load(open(prev_file, encoding="utf-8")):
            prev_sources[t["new_path"]] = t["sources"]
    tracks = {}
    for url, pages in uses.items():
        fname = unquote(url.rsplit("/", 1)[-1])
        if url.startswith(base):
            # URL đã thuộc kho mới: lấy thẳng đường dẫn, không phân loại lại
            rel = unquote(url[len(base):])
            parts = rel.split("/")
            cat, new_name = parts[1], parts[-1]
            key = "path:" + rel
            orig = fname
            # tìm tên gốc từ tracks.json trước đó (nếu có)
            for pp, srcs in prev_sources.items():
                if pp == rel and srcs:
                    orig = unquote(srcs[0].rsplit("/", 1)[-1])
                    break
        else:
            key = unicodedata.normalize("NFC", fname).strip().lower()
            new_name = slug_filename(unicodedata.normalize("NFC", fname).strip())
            cat, orig = category(fname), fname
            key = "path:" + f"lovecard/{cat}/{new_name}"
        t = tracks.setdefault(key, {
            "original_name": orig, "new_file": new_name,
            "category": cat, "sources": [], "pages": set()})
        t["sources"].append(url)
        t["pages"] |= pages
    rows = []
    for t in tracks.values():
        rel = f"lovecard/{t['category']}/{t['new_file']}"
        t["new_path"] = rel
        t["new_url"] = base + quote(rel)
        # gộp URL cũ đã ghi nhận trước đây, bỏ URL trùng với URL mới
        merged = list(dict.fromkeys(prev_sources.get(rel, []) + t["sources"]))
        t["sources"] = [u for u in merged if u != t["new_url"]] or merged
        t["pages"] = sorted(t["pages"])
        t["page_count"] = len(t["pages"])
        rows.append(t)
    rows.sort(key=lambda t: (-t["page_count"], t["new_file"]))

    os.makedirs(os.path.join(ROOT, "lovecard"), exist_ok=True)
    with open(os.path.join(ROOT, "lovecard", "tracks.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    lines = ["# Nhạc nền web LoveCard đang dùng (sinh tự động bởi scripts/lovecard_migration.py)", "",
             "Chép file mp3 tương ứng vào cột **Đặt tại**, rồi chạy `build_index.py`.",
             "Cột **Số trang** = số trang trên lovecard.click đang dùng bài đó.", "",
             "| Số trang | Tên gốc trên web | Đặt tại | Nguồn hiện tại |", "|---:|---|---|---|"]
    for t in rows:
        src = "<br>".join(s.replace("|", "%7C") for s in t["sources"])
        lines.append(f"| {t['page_count']} | {t['original_name']} | `{t['new_path']}` | {src} |")
    lines += ["", "## Thay link trong web", "",
              "Sau khi push repo, thay `src` của thẻ `<audio><source>` bằng cột URL mới trong",
              "`lovecard/tracks.json` (`new_url`). Các URL cũ có xuống dòng/dấu cách ở giữa",
              "là lý do nhạc không chạy ở nhiều trang."]
    with open(os.path.join(ROOT, "lovecard", "TRACKS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{len(rows)} bài, {sum(len(p) for p in uses.values())} lượt dùng -> lovecard/TRACKS.md, lovecard/tracks.json")
    for t in rows[:60]:
        print(f"{t['page_count']:4d}  {t['new_path']}")


if __name__ == "__main__":
    main()
