import io
import os
from urllib.parse import urlparse
from flask import Flask, abort, make_response, render_template, request, send_file, send_from_directory
from werkzeug.utils import safe_join

try:
    from PIL import Image, ImageOps
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

template_dir = os.path.join(BASE_DIR, "templates")
if not os.path.isdir(template_dir):
    template_dir = BASE_DIR

app = Flask(__name__, template_folder=template_dir)

# ==============================================================================
# CONFIGURATION (Change placeholders below or set via Vercel Environment Vars)
# ==============================================================================
SITE_NAME = os.environ.get("SITE_NAME", "cdn")
GITHUB_URL = os.environ.get("GITHUB_URL", "https://github.com/your-username/your-repo")

# Comma-separated allowed domains for hotlink & CORS protection (subdomains match automatically).
# Leave empty ("*") to allow any website to embed your images.
ALLOWED_DOMAINS = [
    d.strip().lower()
    for d in os.environ.get("ALLOWED_DOMAINS", "yourdomain.com,vercel.app,localhost,127.0.0.1").split(",")
    if d.strip()
]

# Optional secret key to lock the "/" dashboard (e.g. visit /?key=your_secret once).
# Leave empty to keep the "/" dashboard public.
ADMIN_KEY = os.environ.get("ADMIN_KEY", "").strip()

RESIZABLE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def format_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024 or unit == "GB":
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{size_bytes} B"
        size_bytes /= 1024
    return f"{size_bytes:.1f} GB"


def is_allowed_host(hostname: str) -> bool:
    if not hostname or "*" in ALLOWED_DOMAINS:
        return True
    hostname = hostname.split(":")[0].lower()
    if hostname == request.host.split(":")[0].lower():
        return True
    return any(hostname == d or hostname.endswith("." + d) for d in ALLOWED_DOMAINS)


def check_hotlink() -> bool:
    """Block unauthorized third-party sites from hotlinking images."""
    referer = request.headers.get("Referer")
    if not referer:
        return True  # Allow direct browser navigation
    parsed = urlparse(referer)
    return is_allowed_host(parsed.netloc)


@app.route("/")
def index():
    if ADMIN_KEY:
        provided_key = request.args.get("key") or request.cookies.get("cdn_key")
        if provided_key != ADMIN_KEY:
            abort(403)

    files = []
    for root, _, filenames in os.walk(IMAGES_DIR):
        for name in sorted(filenames):
            if not name.startswith("."):
                full_path = os.path.join(root, name)
                rel = os.path.relpath(full_path, IMAGES_DIR).replace("\\", "/")
                size_bytes = os.path.getsize(full_path)
                ext = os.path.splitext(name)[1].lower()
                files.append({
                    "path": rel,
                    "name": name,
                    "size": format_size(size_bytes),
                    "resizable": ext in RESIZABLE_EXTS,
                })

    resp = make_response(
        render_template("index.html", files=files, site_name=SITE_NAME, github_url=GITHUB_URL)
    )
    if ADMIN_KEY and request.args.get("key") == ADMIN_KEY:
        resp.set_cookie("cdn_key", ADMIN_KEY, max_age=30 * 86400, httponly=True, samesite="Lax")
    return resp


@app.route("/images/<path:filename>")
@app.route("/<path:filename>")
def serve_image(filename):
    if not check_hotlink():
        abort(403)

    safe_path = safe_join(IMAGES_DIR, filename)
    if not safe_path or not os.path.isfile(safe_path):
        abort(404)

    ext = os.path.splitext(safe_path)[1].lower()
    w = request.args.get("w", type=int)
    h = request.args.get("h", type=int)
    q = request.args.get("q", default=82, type=int)

    # On-the-fly image resizing & WebP compression when ?w= or ?h= is passed
    if HAS_PILLOW and ext in RESIZABLE_EXTS and (w or h):
        w = min(max(w, 16), 3840) if w else None
        h = min(max(h, 16), 3840) if h else None
        q = min(max(q, 10), 100)

        with Image.open(safe_path) as img:
            img = ImageOps.exif_transpose(img)
            orig_w, orig_h = img.size

            if w and h:
                img.thumbnail((w, h), Image.Resampling.LANCZOS)
            elif w and w < orig_w:
                new_h = max(1, int(orig_h * (w / orig_w)))
                img = img.resize((w, new_h), Image.Resampling.LANCZOS)
            elif h and h < orig_h:
                new_w = max(1, int(orig_w * (h / orig_h)))
                img = img.resize((new_w, h), Image.Resampling.LANCZOS)

            buf = io.BytesIO()
            img.save(buf, format="WEBP", quality=q, method=4)
            buf.seek(0)
            response = make_response(send_file(buf, mimetype="image/webp"))
    else:
        response = make_response(send_from_directory(IMAGES_DIR, filename, conditional=True))

    # CORS headers
    origin = request.headers.get("Origin")
    if origin and is_allowed_host(urlparse(origin).netloc):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    elif not origin:
        response.headers["Access-Control-Allow-Origin"] = "*"

    # Hardened security & smart caching headers
    response.headers["Cache-Control"] = "public, max-age=86400, stale-while-revalidate=604800"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; sandbox"
    return response


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
