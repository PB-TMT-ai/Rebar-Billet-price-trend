"""
Extract inventory costs from uploaded image using OCR and update inventory_costs.json.

Usage:
    python scripts/extract_inventory_from_image.py <path_to_image>

Reads the "Avg Inventory Cost(12-32MM)" column from the image and updates
the JSON file with the new date's data.

Note: OCR is best-effort. Values are flagged with _needs_manual_review=true
for any newly extracted date so a human can verify before using.
"""

import sys
import os
import re
import json
from datetime import date
from typing import Any

try:
    import pytesseract
    from PIL import Image
except ImportError:
    print("[ERROR] pytesseract + Pillow required. Install: pip install pytesseract Pillow")
    sys.exit(1)


MARGIN_DIR = "daily rebar prices/margin dashboard"
JSON_PATH = os.path.join(MARGIN_DIR, "inventory_costs.json")

PLANTS_ORDER = [
    ("API Ispat", "Fe 550"),
    ("SKA Ispat", "Fe 550"),
    ("Aditya Industries", "Fe 550"),
    ("ASUL-Gwalior", "Fe 550"),
    ("ASUL-Gwalior", "Fe 550D-LRF"),
    ("Amba Shakti", "Fe 550"),
    ("Real Ispat", "Fe 550D-LRF"),
    ("German Steel", "Fe 550"),
    ("N N Ispat", "Fe 550"),
]


def parse_image_date(filename: str) -> str | None:
    base = os.path.basename(filename)
    m = re.match(r"(\d+)(?:st|nd|rd|th)?\s*(\w+)['`\u2019]?(\d{2})\.png", base, re.IGNORECASE)
    if not m:
        return None
    day = int(m.group(1))
    mon_str = m.group(2)[:3].title()
    yr = 2000 + int(m.group(3))
    months = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
              "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
    mon = months.get(mon_str)
    if not mon:
        return None
    try:
        return date(yr, mon, day).strftime("%Y-%m-%d")
    except ValueError:
        return None


def extract_numbers_from_image(img_path: str) -> list[int]:
    img = Image.open(img_path)
    text = pytesseract.image_to_string(img, config="--psm 6")
    numbers = []
    for token in re.findall(r"\d[\d,]*", text):
        cleaned = token.replace(",", "")
        if cleaned.isdigit():
            n = int(cleaned)
            if 40000 <= n <= 80000:
                numbers.append(n)
    return numbers


def update_json(image_path: str) -> None:
    date_str = parse_image_date(image_path)
    if not date_str:
        print(f"[ERROR] Cannot parse date from filename: {image_path}")
        sys.exit(1)

    print(f"[INFO] Processing image: {image_path} (date: {date_str})")

    if os.path.exists(JSON_PATH):
        with open(JSON_PATH) as f:
            data = json.load(f)
    else:
        data = {"by_date": {}}

    if "by_date" not in data:
        data["by_date"] = {}

    if date_str in data["by_date"]:
        print(f"[INFO] Date {date_str} already in JSON, skipping.")
        return

    print("[INFO] Running OCR...")
    numbers = extract_numbers_from_image(image_path)
    print(f"[INFO] Found {len(numbers)} candidate numbers")

    if len(numbers) < 9:
        print(f"[WARN] Not enough numbers extracted. Using previous date as fallback.")
        all_dates = sorted(data["by_date"].keys(), reverse=True)
        if all_dates:
            prev = data["by_date"][all_dates[0]]
            data["by_date"][date_str] = {
                "image_file": os.path.basename(image_path),
                "costs": prev["costs"].copy(),
                "grade_averages": prev.get("grade_averages", {}).copy(),
                "_needs_manual_review": True,
            }
    else:
        candidates = numbers[-11:] if len(numbers) >= 11 else numbers[-9:]

        costs: dict[str, Any] = {}
        for i, (plant, grade) in enumerate(PLANTS_ORDER):
            if i < len(candidates):
                costs[f"{plant}|{grade}"] = candidates[i]

        grade_averages: dict[str, Any] = {}
        if len(candidates) >= 11:
            grade_averages = {
                "Fe 550": candidates[9],
                "Fe 550D-LRF": candidates[10],
            }

        data["by_date"][date_str] = {
            "image_file": os.path.basename(image_path),
            "costs": costs,
            "grade_averages": grade_averages,
            "_needs_manual_review": True,
            "_ocr_raw_numbers": candidates,
        }
        print(f"[INFO] Extracted {len(costs)} plant costs (review recommended)")

    with open(JSON_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[INFO] Updated {JSON_PATH}")


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"[ERROR] Image not found: {image_path}")
        sys.exit(1)

    update_json(image_path)


if __name__ == "__main__":
    main()
