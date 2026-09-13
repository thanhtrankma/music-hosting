# music-hosting – kho nhạc nền dùng qua jsDelivr CDN

Repo GitHub chứa file nhạc nền (mp3) cho các website thiệp mời. File được phục vụ
miễn phí qua jsDelivr:

```
https://cdn.jsdelivr.net/gh/<github_user>/<repo>@<branch>/<project>/<the-loai>/<ten-file>.mp3
```

## Cấu trúc thư mục

```
music-hosting/
├── config.json            # tên user/repo GitHub, branch -> dùng để sinh URL
├── index.json             # SINH TỰ ĐỘNG: danh sách file + URL CDN
├── URLS.md                # SINH TỰ ĐỘNG: bảng URL để copy vào web
├── lovecard/              # nhạc cho project LoveCard (lovecard.click)
│   ├── wedding-vn/        #   nhạc cưới tiếng Việt
│   ├── wedding-en/        #   nhạc cưới quốc tế
│   ├── instrumental/      #   nhạc không lời, piano, giao hưởng
│   ├── birthday/          #   sinh nhật, thôi nôi
│   ├── sfx/               #   hiệu ứng ngắn (chuông, pháo...)
│   └── TRACKS.md          #   SINH TỰ ĐỘNG: các bài web LoveCard đang dùng
├── _shared/               # nhạc dùng chung cho mọi project
│   ├── instrumental/
│   └── sfx/
├── <project-khac>/        # thêm project mới = thêm 1 thư mục cùng cấp
│   └── <the-loai>/
└── scripts/
    ├── normalize.py           # đổi tên file: bỏ dấu, bỏ khoảng trắng, chữ thường
    ├── build_index.py         # sinh index.json + URLS.md
    └── lovecard_migration.py  # quét web LoveCard đã clone -> lovecard/TRACKS.md
```

Quy ước: **thư mục cấp 1 = project**, **cấp 2 = thể loại**, tên file chỉ gồm
`a-z 0-9 - _ .` (script `normalize.py` lo việc này).

## Quy trình thêm nhạc

1. Chép file mp3 vào đúng thư mục `<project>/<the-loai>/`.
2. Chuẩn hoá tên file và sinh bảng URL:

   ```bash
   python3 scripts/normalize.py
   python3 scripts/build_index.py
   ```

3. Commit và push:

   ```bash
   git add -A
   git commit -m "Thêm nhạc ..."
   git push
   ```

4. Copy URL trong `URLS.md` (hoặc `index.json`) vào thẻ `<audio>` của web:

   ```html
   <audio id="myAudio" loop>
     <source src="https://cdn.jsdelivr.net/gh/USER/music-hosting@main/lovecard/wedding-vn/ten-bai.mp3" type="audio/mpeg">
   </audio>
   ```

## Giới hạn cần nhớ

- jsDelivr chỉ phục vụ file **≤ 20 MB** từ GitHub; `build_index.py` sẽ cảnh báo file vượt ngưỡng.
  Nén mp3 về 128 kbps nếu cần (`ffmpeg -i in.mp3 -b:a 128k out.mp3`).
- GitHub khuyến nghị repo dưới 1 GB; tách repo mới khi kho quá lớn.
- URL không có `@branch` (`/gh/user/repo/file`) bị cache lâu; dùng `@main`
  hoặc `@<tag>` để kiểm soát. Sau khi ghi đè file cùng tên, đổi tag hoặc dùng
  URL purge: `https://purge.jsdelivr.net/gh/USER/REPO@main/duong/dan.mp3`.
- Tên file có dấu cách / dấu tiếng Việt từng làm hỏng link trên web cũ
  (URL bị cắt tại dấu cách). Luôn chạy `normalize.py` trước khi push.

## Lần đầu tạo repo trên GitHub

```bash
cd music-hosting
git init -b main
git add -A
git commit -m "Khởi tạo kho nhạc nền"
git remote add origin https://github.com/<github_user>/music-hosting.git
git push -u origin main
```

Sửa `github_user` trong `config.json` cho đúng tài khoản của bạn trước khi
chạy `build_index.py`.
