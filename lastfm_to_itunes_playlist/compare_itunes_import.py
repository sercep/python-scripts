import csv
import unicodedata
from pathlib import Path

# =========================
# НАСТРОЙКИ
# =========================

SOURCE_FILE = "new.txt"   # твой файл, который ты импортировал
ITUNES_EXPORT_FILE = "old.txt"   # экспорт уже реально добавленного плейлиста

OUTPUT_MISSING = "missing2.txt"
OUTPUT_FOUND = "found.txt"

ENCODING = "utf-16"  # iTunes TXT обычно UTF-16
DELIMITER = "\t"

# =========================
# НОРМАЛИЗАЦИЯ
# =========================

def normalize(text: str) -> str:
    if text is None:
        return ""

    text = str(text).strip()
    text = unicodedata.normalize("NFKC", text)
    text = text.casefold()

    # схлопываем множественные пробелы
    text = " ".join(text.split())

    return text

def make_key(row: dict):
    track = normalize(row.get("Название", ""))
    artist = normalize(row.get("Артист", ""))
    album = normalize(row.get("Альбом", ""))

    return (artist, track, album)

# =========================
# ЧТЕНИЕ TXT
# =========================

def read_itunes_txt(path: str):
    rows = []

    with open(path, "r", encoding=ENCODING, newline="") as f:
        reader = csv.DictReader(f, delimiter=DELIMITER)

        for row in reader:
            track = row.get("Название", "").strip()
            artist = row.get("Артист", "").strip()
            album = row.get("Альбом", "").strip()

            if not track or not artist:
                continue

            rows.append({
                "Название": track,
                "Артист": artist,
                "Альбом": album,
                "_key": make_key(row)
            })

    return rows

# =========================
# ЗАГРУЗКА
# =========================

source_rows = read_itunes_txt(SOURCE_FILE)
itunes_rows = read_itunes_txt(ITUNES_EXPORT_FILE)

source_keys = {row["_key"]: row for row in source_rows}
itunes_keys = {row["_key"]: row for row in itunes_rows}

missing = []
found = []

for key, row in source_keys.items():
    if key in itunes_keys:
        found.append(row)
    else:
        missing.append(row)

# =========================
# СОХРАНЕНИЕ РЕЗУЛЬТАТОВ
# =========================

def write_result(path: str, rows: list):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["Название", "Артист", "Альбом"])

        for row in sorted(rows, key=lambda x: (
            x["Артист"].casefold(),
            x["Альбом"].casefold(),
            x["Название"].casefold()
        )):
            writer.writerow([
                row["Название"],
                row["Артист"],
                row["Альбом"]
            ])

write_result(OUTPUT_MISSING, missing)
write_result(OUTPUT_FOUND, found)

# =========================
# СТАТИСТИКА
# =========================

print(f"Исходных уникальных треков: {len(source_keys)}")
print(f"Найдено в iTunes: {len(found)}")
print(f"Пропущено iTunes: {len(missing)}")
print()
print(f"Сохранено:")
print(f" - {OUTPUT_FOUND}")
print(f" - {OUTPUT_MISSING}")