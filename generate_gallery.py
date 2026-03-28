#!/usr/bin/env python3
"""
generate_gallery.py
-------------------
Scans imgs/gallery/ for image files and writes/updates gallery.json.

Run once manually, or let GitHub Actions run it automatically on every push.

Category auto-detection (by filename prefix):
  Field*                          → fieldwork
  Talk*, SGS*, Certificate*,
  Event*, WhatsApp*               → talks
  Lab*                            → specimens
  anything else                   → research

If gallery.json already exists, existing entries keep their metadata
(title, description, category overrides). Only truly new files get
auto-generated metadata.
"""

import json
import os
import re
from pathlib import Path

GALLERY_DIR = Path("imgs/gallery")
OUTPUT_FILE = Path("gallery.json")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def detect_category(filename: str) -> str:
    name = filename.lower()
    if name.startswith("field"):
        return "fieldwork"
    if name.startswith(("talk", "sgs", "certificate", "event", "whatsapp")):
        return "talks"
    if name.startswith("lab"):
        return "specimens"
    return "research"


def url_encode_filename(filename: str) -> str:
    """Percent-encode spaces and parentheses so the src attr is a valid URL."""
    return filename.replace(" ", "%20").replace("(", "%28").replace(")", "%29")


def default_titles(filename: str, category: str) -> tuple[str, str]:
    """Return (titleEn, titleAr) based on category."""
    mapping = {
        "fieldwork":  ("Geological Field Work",          "العمل الجيولوجي الميداني"),
        "talks":      ("Academic Talk / Event",           "محاضرة أو فعالية أكاديمية"),
        "specimens":  ("Micropaleontology Lab Work",      "العمل المختبري في الأحياء الدقيقة القديمة"),
        "research":   ("Research Site",                   "موقع بحثي"),
    }
    return mapping.get(category, ("Photo", "صورة"))


def default_descs(category: str) -> tuple[str, str]:
    """Return (descEn, descAr) based on category."""
    mapping = {
        "fieldwork":  ("Field research and geological investigation", "بحث ميداني وتحقيق جيولوجي"),
        "talks":      ("Invited talk, seminar or academic event",      "محاضرة مدعوة أو ندوة أكاديمية"),
        "specimens":  ("Fossil specimens and lab analysis",            "عينات أحفورية وتحليل مختبري"),
        "research":   ("Geological research site",                     "موقع البحث الجيولوجي"),
    }
    return mapping.get(category, ("", ""))


def main():
    # ── Load existing gallery.json (to preserve manual overrides) ──────────────
    existing: dict[str, dict] = {}
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, encoding="utf-8") as f:
                for entry in json.load(f):
                    # key = bare filename (no path prefix)
                    key = Path(entry["src"]).name
                    existing[key] = entry
            print(f"Loaded {len(existing)} existing entries from {OUTPUT_FILE}")
        except Exception as e:
            print(f"Warning: could not parse existing {OUTPUT_FILE}: {e}")

    # ── Scan gallery directory ─────────────────────────────────────────────────
    if not GALLERY_DIR.exists():
        print(f"Error: directory '{GALLERY_DIR}' not found. "
              f"Run this script from the project root.")
        raise SystemExit(1)

    image_files = sorted(
        [f for f in GALLERY_DIR.iterdir()
         if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS],
        key=lambda p: p.name.lower()
    )

    print(f"Found {len(image_files)} image(s) in {GALLERY_DIR}/")

    # ── Build output list ──────────────────────────────────────────────────────
    items = []
    for img in image_files:
        filename = img.name
        encoded  = url_encode_filename(filename)
        src      = f"imgs/gallery/{encoded}"

        if filename in existing:
            # Preserve everything; just make sure src is up-to-date
            entry = dict(existing[filename])
            entry["src"] = src
        else:
            category = detect_category(filename)
            title_en, title_ar = default_titles(filename, category)
            desc_en,  desc_ar  = default_descs(category)
            entry = {
                "src":      src,
                "category": category,
                "titleEn":  title_en,
                "titleAr":  title_ar,
                "descEn":   desc_en,
                "descAr":   desc_ar,
            }
            print(f"  + NEW: {filename}  →  category={category}")

        items.append(entry)

    # ── Write gallery.json ─────────────────────────────────────────────────────
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"\nWrote {len(items)} entries to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
