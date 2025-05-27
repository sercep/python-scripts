import os
import re
import openpyxl
from openpyxl import Workbook
from collections import defaultdict

DAILY_NOTES_DIR = r"C:\Users\sercep\Documents\obsidian\sercep\Daily"

# Excel
wb = Workbook()
ws = wb.active
ws.title = "Music Log"
ws.append(["Artist", "Title", "Year", "Type", "Rating", "Source", "Tags", "Listens", "Dates"])

# Регулярки
release_line_re = re.compile(r"\[\[([^\[\]-]+?)\s*-\s*(.+?)\s*(?:\((\d{4})\))?\]\](?:\s*(.*))?")
rating_re = re.compile(r"(?:где-то\s*)?(\d\+?)")
source_re = re.compile(r"\*(.*?)\*")
type_re = re.compile(r"\b(Album|EP|Compilation|Single)\b", re.IGNORECASE)
tags_re = re.compile(r"(#[\w/]+)", re.IGNORECASE)

# Словарь релизов: ключ — (artist, title, year)
releases = {}

def process_release_block(release_lines, date):
    full_block = "".join(release_lines)
    match = release_line_re.search(full_block)
    if not match:
        return

    artist = match.group(1).strip()
    title = match.group(2).strip()
    year = match.group(3)
    trailing = match.group(4) or ""

    key = (artist, title, year)

    # Инициализируем, если впервые
    if key not in releases:
        releases[key] = {
            "artist": artist,
            "title": title,
            "year": year or "",
            "type": "",
            "rating": "",
            "source": "",
            "tags": set(),
            "dates": set(),
            "count": 0
        }

    # Обновление данных
    block_text = full_block + " " + trailing
    releases[key]["count"] += 1
    releases[key]["dates"].add(date)

    # Последние по времени значения перезаписывают
    type_match = type_re.search(block_text)
    if type_match:
        releases[key]["type"] = type_match.group(1)

    source_match = source_re.search(block_text)
    if source_match:
        releases[key]["source"] = source_match.group(1)

    rating_match = rating_re.findall(block_text)
    if rating_match:
        releases[key]["rating"] = rating_match[-1]

    tags_found = tags_re.findall(block_text)
    releases[key]["tags"].update(t.lower() for t in tags_found)

# Обработка всех файлов
for filename in sorted(os.listdir(DAILY_NOTES_DIR)):
    if not filename.endswith(".md"):
        continue

    date = filename[:10] if re.match(r"\d{4}-\d{2}-\d{2}", filename) else "unknown"
    path = os.path.join(DAILY_NOTES_DIR, filename)

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    inside_listen_block = False
    buffer = []

    for line in lines:
        if "Послушал" in line:
            inside_listen_block = True
            continue

        if inside_listen_block:
            if line.strip().startswith("- "):
                if buffer:
                    process_release_block(buffer, date)
                    buffer = [line]
                else:
                    buffer.append(line)
            elif line.strip() == "":
                continue
            else:
                buffer.append(line)

    if buffer:
        process_release_block(buffer, date)

# Запись в Excel
for data in releases.values():
    ws.append([
        data["artist"],
        data["title"],
        data["year"],
        data["type"],
        data["rating"],
        data["source"],
        ", ".join(sorted(data["tags"])),
        data["count"],
        ", ".join(sorted(data["dates"]))
    ])

# Сохраняем
output_path = os.path.join(os.getcwd(), "obsidian_music.xlsx")
wb.save(output_path)
print("Сохранено в:", output_path)
