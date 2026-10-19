# ⚡ Minimal Flask Image CDN

A lightweight, zero-database personal image & asset CDN built with **Flask** and designed to run for free on **Vercel**. Drop images into the `images/` folder via GitHub and use them across all your websites.

---

## ✨ Features

- **Zero Database / Git-Powered** — Upload images directly to the `images/` folder on GitHub.
- **Root-Level Clean URLs** — `images/logo.svg` is served directly at `https://your-cdn.vercel.app/logo.svg`.
- **On-the-Fly Resizing & WebP Compression** — Append `?w=400` (or `?h=400&q=80`) to any `.jpg`/`.png`/`.webp` URL to automatically resize and convert it to WebP on the fly.
- **Minimal Dark Dashboard (`/`)** — Instant `/` keyboard filter, file size badges, full-screen lightbox preview, and one-click URL copy.
- **Hardened by Default** — Built-in hotlink/CORS domain whitelist, SVG script sandboxing (`Content-Security-Policy`), `nosniff`, and optional secret key protection for the `/` index page.

---

## 📁 Project Structure

```text
├── images/
│   └── placeholder.svg    # Drop your images/SVGs here
├── templates/
│   └── index.html         # Minimal dark UI for /
├── app.py                 # Flask server, resizing & security headers
├── requirements.txt       # flask, Pillow
└── vercel.json            # Zero-config Vercel bundling
```

---

## 🚀 Deploy to Vercel (Free Plan)

1. Push this repository to GitHub.
2. Import the repository on [Vercel](https://vercel.com/new).
3. *(Optional)* Configure environment variables in **Vercel → Settings → Environment Variables**:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `SITE_NAME` | `cdn` | Header & page title shown on `/` |
| `GITHUB_URL` | `https://github.com/your-username/your-repo` | Link for the GitHub icon in the footer |
| `ALLOWED_DOMAINS` | `yourdomain.com,vercel.app,localhost,127.0.0.1` | Comma-separated domains allowed to embed your images (use `*` to allow all) |
| `ADMIN_KEY` | *(empty — public)* | If set (e.g. `mysecret`), locks `/` unless you visit `/?key=mysecret` once |

---

## 🖼️ Usage

### 1. Direct Image URL
Upload `avatar.jpeg` into `images/` on GitHub, then use:
```html
<img src="https://your-cdn.vercel.app/avatar.jpeg" alt="Avatar">
```

### 2. On-the-Fly Resized WebP
Add `?w=` (width), `?h=` (height), and optional `&q=` (quality, `10`–`100`, default `82`):
```html
<img src="https://your-cdn.vercel.app/avatar.jpeg?w=256" alt="Avatar">
```

---

## 💻 Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
FLASK_DEBUG=1 python app.py
```
Then open `http://localhost:5000`.
