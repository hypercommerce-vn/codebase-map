# Website Codebase Map

Trang giới thiệu tĩnh, song ngữ (`/` tiếng Việt, `/en/` tiếng Anh), kèm bản đồ demo
thật ở `/demo/`. Không backend, không cookie, không tải gì từ CDN.

Mỗi lần build, `build.py` dựng đồ thị từ chính `codebase_map/` trong repo này: bản đồ demo,
các con số trên trang và đoạn output terminal ở hero đều là kết quả thật, không gõ tay.

```
website/
├── build.py            # dựng site vào website/dist/
├── content.py          # toàn bộ chữ trên trang, hai ngôn ngữ cùng key
├── src/                # template HTML, CSS, JS, favicon, 404
├── deploy/nginx.conf   # cấu hình nginx dùng chung cho VPS và Docker
├── deploy/deploy.sh    # build + rsync lên VPS
├── Dockerfile          # build context = gốc repo
└── docker-compose.yml
```

## Build và xem thử trên máy

Cần Python 3.10+ có PyYAML (venv dev của repo là đủ: `pip install -e ".[dev]"`).

```bash
python website/build.py
python -m http.server 8000 --directory website/dist
```

Mở http://localhost:8000. Sửa chữ trong `content.py`; hai ngôn ngữ phải có cùng bộ key,
nếu lệch thì build dừng và báo key nào thiếu.

## Deploy cách 1: VPS có nginx (khuyên dùng)

Yêu cầu trên VPS: Ubuntu/Debian có `nginx`, `rsync`, `certbot` (`python3-certbot-nginx`),
một user SSH có sudo, và bản ghi DNS A/AAAA của tên miền trỏ về VPS.

Lần đầu (cài site nginx, tạo `/var/www/codebase-map`, reload nginx):

```bash
DEPLOY_HOST=deploy@IP_VPS DOMAIN=ten-mien-cua-ban website/deploy/deploy.sh --setup
ssh deploy@IP_VPS 'sudo certbot --nginx -d ten-mien-cua-ban'
```

Các lần sau chỉ cần build và đẩy file:

```bash
DEPLOY_HOST=deploy@IP_VPS DOMAIN=ten-mien-cua-ban website/deploy/deploy.sh
```

Biến tuỳ chọn: `WEBROOT` (mặc định `/var/www/codebase-map`), `PYTHON` (mặc định `python3`,
ví dụ `PYTHON=.venv/bin/python`).

Các chốt an toàn của script:

- `WEBROOT` phải là đúng một thư mục nằm ngay dưới `/var/www` hoặc `/srv`. Script dùng
  `rsync --delete` (file nào không còn trong `dist/` sẽ bị xoá khỏi web root), nên nó chỉ đẩy
  file vào thư mục do chính `--setup` tạo ra, có file đánh dấu `.codebase-map-webroot`.
- `--setup` không ghi đè file site nginx đã có, vì certbot đã thêm khối HTTPS vào file đó.
  Muốn thay thì chạy lại với `FORCE=1` rồi chạy certbot lần nữa.
- Nếu `nginx -t` báo lỗi, script trả cấu hình về như cũ và không reload nginx.

## Deploy cách 2: Docker

```bash
SITE_URL=https://ten-mien-cua-ban docker compose -f website/docker-compose.yml up -d --build
```

Container nghe ở `127.0.0.1:8080` (đổi bằng `WEB_PORT`). HTTPS do reverse proxy sẵn có trên
VPS lo (nginx, Caddy, Traefik), ví dụ với nginx:

```nginx
location / { proxy_pass http://127.0.0.1:8080; proxy_set_header Host $host; }
```

## Bảo mật

`deploy/nginx.conf` gửi CSP chặt cho mọi trang (chỉ tải file cùng origin, không script inline).
Riêng `/demo/` là file HTML một-trang do CBM xuất ra, có script và style inline, nên CSP ở đó
cho phép `'unsafe-inline'` và chỉ cho nhúng trong chính site (`frame-ancestors 'self'`).
