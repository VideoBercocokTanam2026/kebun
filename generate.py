#!/usr/bin/env python3
"""
Generator situs Video Bercocok Tanam.

Cara pakai:
    python3 generate.py

Baca semua video dari videos.json, lalu otomatis membuat:
  - index.html                         (halaman utama, grid video)
  - bercocok-tanam-part-N.html         (1 halaman per video)

Tidak perlu diedit manual — cukup edit videos.json (dan taruh gambar
cover di folder covers/ kalau mau og:image custom), lalu jalankan file
ini (atau biarkan GitHub Actions yang menjalankannya otomatis).

PERUBAHAN (fix bug only_new=True):
  1. Halaman video sekarang SELALU ditulis ulang tiap run (bukan cuma
     yang baru), supaya perubahan judul/deskripsi/cover ikut ter-update
     meski slug-nya tidak berubah.
  2. Halaman lama yang slug-nya sudah tidak dipakai lagi di videos.json
     (misalnya karena judul video diedit sehingga slug berubah) akan
     dihapus otomatis dari hasil deploy — TAPI hanya kalau file itu
     memang mengandung marker GENERATED_MARKER di bawah, supaya halaman
     statis lain yang sengaja ditambahkan manual tidak ikut kehapus.
     (Halaman orphan LAMA yang dibuat sebelum fix ini tidak akan
     kehapus otomatis karena tidak punya marker tsb — lihat catatan di
     README/handover soal daftar file yang perlu dihapus manual.)
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
GITHUB_OWNER = "viral18plus"
REPOSITORIES = {
    "indonesia": "indonesia",
    "papua": "papua",
}
SITE_REPO = "papua"
def build_og_image(repo, slug, extension="jpg"):
    target = REPOSITORIES[repo]
    return f"https://{GITHUB_OWNER}.github.io/{target}/covers/{slug}.{extension}"


SITE_BASE_URL = f"https://{GITHUB_OWNER}.github.io/{REPOSITORIES[SITE_REPO]}/"
DEFAULT_DESC = "Kumpulan video bercocok tanam berepisode, dari bibit sampai panen."

# Marker penanda "halaman ini dibuat oleh generate.py". Harus ada di
# templates/video.template.html (lihat instruksi terpisah) supaya
# cleanup_orphan_pages() tahu file mana yang aman dihapus otomatis.
GENERATED_MARKER = "<!-- generated-by-repopilot -->"


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def load_videos():
    with open(os.path.join(ROOT, "videos.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def cover_image_url(slug, drive_id, og_image=""):
    """Gunakan ogImage dari videos.json bila valid; jika kosong, cari cover lokal.
    Tidak menggunakan thumbnail Google Drive sebagai OG Image."""
    expected_prefix = f"{SITE_BASE_URL}covers/"
    if og_image and og_image.startswith(expected_prefix):
        return og_image
    for ext in ("jpg", "jpeg", "png", "webp"):
        cover_path = os.path.join(ROOT, "covers", f"{slug}.{ext}")
        if os.path.exists(cover_path):
            return build_og_image(SITE_REPO, slug, ext)
    return ""


def build_index(videos):
    template_path = os.path.join(ROOT, "templates", "index.template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    latest = videos[0] if videos else None
    if latest:
        slug = slugify(latest["judul"])
        og_image = cover_image_url(slug, latest.get("driveId", ""), latest.get("ogImage", ""))
    else:
        og_image = f"{SITE_BASE_URL}cover.jpg"
    html = html.replace("__OG_IMAGE__", og_image)

    out_path = os.path.join(ROOT, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("generated index.html")


def cleanup_orphan_pages(valid_slugs):
    """Hapus halaman video lama yang slug-nya sudah tidak ada lagi di
    videos.json saat ini (biasanya karena judul diedit / video dihapus).
    Hanya menghapus file .html di root yang mengandung GENERATED_MARKER,
    supaya halaman statis lain yang sengaja ditaruh manual tidak ikut
    kehapus. Ini menghapus dari working directory runner sebelum
    di-upload sebagai artifact Pages, jadi halaman orphan tidak ikut
    ter-deploy lagi mulai run ini."""
    removed = []
    for fname in os.listdir(ROOT):
        if not fname.endswith(".html") or fname == "index.html":
            continue
        slug = fname[:-len(".html")]
        if slug in valid_slugs:
            continue

        fpath = os.path.join(ROOT, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue

        if GENERATED_MARKER in content:
            os.remove(fpath)
            removed.append(fname)
    return removed


def build_video_pages(videos):
    """Generate ULANG setiap halaman video tiap run (tidak ada lagi
    skip-if-exists), supaya edit judul/deskripsi/cover selalu
    tercermin di halaman publiknya."""
    template_path = os.path.join(ROOT, "templates", "video.template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    for v in videos:
        slug = slugify(v["judul"])
        out_path = os.path.join(ROOT, f"{slug}.html")

        drive_id = v["driveId"]
        og_image = cover_image_url(slug, drive_id, v.get("ogImage", ""))

        html = template
        html = html.replace("__PAGE_TITLE__", v["judul"])
        html = html.replace("__OG_TITLE__", v["judul"])
        html = html.replace("__OG_DESC__", v.get("deskripsi") or DEFAULT_DESC)
        html = html.replace("__OG_URL__", f"{SITE_BASE_URL}{slug}.html")
        html = html.replace("__OG_IMAGE__", og_image)
        html = html.replace("__VIDEO_ID__", drive_id)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"generated {slug}.html")


def main():
    videos = load_videos()
    if not videos:
        print("videos.json kosong, tidak ada yang digenerate.", file=sys.stderr)
        return

    valid_slugs = {slugify(v["judul"]) for v in videos}

    build_index(videos)

    removed = cleanup_orphan_pages(valid_slugs)
    for fname in removed:
        print(f"removed halaman lama (orphan): {fname}")

    build_video_pages(videos)


if __name__ == "__main__":
    main()
